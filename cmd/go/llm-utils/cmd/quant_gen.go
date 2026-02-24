package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"llm-playground/cmd/go/llm-utils/config"
	"llm-playground/internal/go/api"

	"github.com/spf13/cobra"
)

var (
	quantInputs        []string
	quantOutput        string
	quantLogic         string
	quantLimit         int
	quantCritique      string
	quantRAG           string
	quantRAGProv       string
	onyxProjectID      int
	quantUseAnalyst    bool
	quantSaveAnalysis  string
	quantForceMaxAlign bool
	quantSelfCorrect   bool
	quantDistill       bool
	quantPromptOnly    bool
)

// TimeframeData holds parsed data for a single timeframe
type TimeframeData struct {
	Timeframe string
	Candles   []api.Candle
	Filename  string
}

// genCmd represents the gen command
var genCmd = &cobra.Command{
	Use:   "gen",
	Short: "Generate a TradingView Pine Script strategy from CSV data",
	Long: `Parses a TradingView CSV export and uses a local LLM to generate a corresponding
Pine Script (v5) strategy.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Validate input
		if len(quantInputs) == 0 {
			return fmt.Errorf("at least one input file required via -i flag")
		}

		// Parse all input files
		var allData []TimeframeData

		// 1. First pass to detect timeframes and find baseline
		type inputMeta struct {
			path    string
			tf      string
			minutes int
		}
		var metas []inputMeta
		minMinutes := 999999
		maxMinutes := 0
		for _, inputFile := range quantInputs {
			name, mins := detectTimeframe(inputFile)
			metas = append(metas, inputMeta{inputFile, name, mins})
			if mins > 0 {
				if mins < minMinutes {
					minMinutes = mins
				}
				if mins > maxMinutes {
					maxMinutes = mins
				}
			}
		}

		// 2. Second pass to parse data with adaptive limits
		for _, meta := range metas {
			limit := quantLimit
			if len(quantInputs) > 1 {
				if quantForceMaxAlign {
					// 4090 Mode: Proportional scaling based on MAX units
					// e.g. 1D is 50 -> 1H is 50 * 24 = 1200
					if meta.minutes > 0 {
						limit = (quantLimit * maxMinutes) / meta.minutes
					}
				} else if meta.minutes > minMinutes {
					// Context Saving Mode: Scale down higher units
					adaptiveLimit := (quantLimit * minMinutes) / meta.minutes
					if adaptiveLimit < 40 {
						adaptiveLimit = 40
					}
					limit = adaptiveLimit
				}
			}

			fmt.Printf("📊 Parsing data from: %s (Detected: %s, Limit: %d)\n", meta.path, meta.tf, limit)
			candles, err := api.ParseTradingViewCSV(meta.path, limit)
			if err != nil {
				return fmt.Errorf("failed to parse %s: %w", meta.path, err)
			}
			allData = append(allData, TimeframeData{
				Timeframe: meta.tf,
				Candles:   candles,
				Filename:  filepath.Base(meta.path),
			})
		}

		// Format market data based on number of inputs
		var marketData string
		if len(allData) == 1 {
			// Single file: simple format
			marketData = api.FormatCandlesForLLM(allData[0].Candles)
		} else {
			// Multiple files: MTF format
			marketData = formatMultiTimeframeData(allData)
		}

		// Optional: Stage 1 - Market Analysis with Plutus
		var analystInsight string
		analystModel := config.AppConfig.Quant.AnalystModel
		if analystModel == "" {
			analystModel = "deepseek-r1:32b"
		}

		if quantUseAnalyst {
			if analystModel == "" {
				analystModel = "deepseek-r1:32b"
			}

			fmt.Printf("📈 Stage 1: Analyzing market data with %s...\n", analystModel)
			insight, err := analyzeMarketData(allData, quantLogic)
			if err != nil {
				fmt.Printf("⚠️  Warning: Analyst stage failed: %v\n", err)
				fmt.Println("📝 Continuing with code generation only...")
			} else {
				analystInsight = insight
				fmt.Printf("✅ Market analysis completed (%d chars)\n", len(insight))

				// Optionally save analysis to file
				if quantSaveAnalysis != "" {
					if err := os.WriteFile(quantSaveAnalysis, []byte(insight), 0644); err != nil {
						fmt.Printf("⚠️  Warning: Failed to save analysis: %v\n", err)
					} else {
						fmt.Printf("💾 Analysis saved to: %s\n", quantSaveAnalysis)
					}
				}
			}
		}

		var critiqueData string
		if quantCritique != "" {
			data, err := os.ReadFile(quantCritique)
			if err == nil {
				critiqueData = fmt.Sprintf("\nANALYST CRITIQUE (FIX THESE):\n%s\n", string(data))
			}
		}

		var ragData string
		ragWS := quantRAG
		if ragWS == "" {
			ragWS = config.AppConfig.Quant.RAGWorkspace
		}

		ragProv := quantRAGProv
		if ragProv == "" {
			ragProv = config.AppConfig.Quant.RAGProvider
		}

		query := fmt.Sprintf("Pine Script v6 strategy templates, trailing stop exit rules, and ta.* function pre-calculation for: %s", quantLogic)

		if ragProv == "onyx" && config.AppConfig.Onyx.BaseURL != "" {
			fmt.Printf("🔍 Querying Onyx RAG (%s) for documentation... (Logic: %s)\n", config.AppConfig.Onyx.BaseURL, quantLogic)

			pid := onyxProjectID
			if pid == 0 {
				pid = config.AppConfig.Onyx.ProjectID
			}

			client := api.NewOnyxClient(config.AppConfig.Onyx.BaseURL, config.AppConfig.Onyx.APIKey)
			resp, err := client.Query(config.AppConfig.Onyx.PersonaID, pid, query)
			if err == nil && resp != "" {
				fmt.Printf("📖 Retrieved %d characters of RAG context.\n", len(resp))
				// Truncate RAG data to prevent context window overflow
				if len(resp) > 8000 {
					resp = resp[:8000] + "... (truncated)"
				}
				ragData = fmt.Sprintf("\nDOCUMENTATION CONTEXT (PINE V6 BIBLE & TEMPLATES):\n%s\n", resp)
			} else if err != nil {
				fmt.Printf("⚠️ Onyx RAG Error: %v\n", err)
			}
		} else if ragProv == "anything" && ragWS != "" && config.AppConfig.Anything.BaseURL != "" {
			fmt.Printf("🔍 Querying AnythingLLM RAG Workspace (%s) for documentation...\n", ragWS)
			client := api.NewAnythingClient(config.AppConfig.Anything.BaseURL, config.AppConfig.Anything.APIKey)
			resp, err := client.QueryWorkspace(ragWS, query)
			if err == nil && resp != "" {
				ragData = fmt.Sprintf("\nDOCUMENTATION CONTEXT (PINE V6 BIBLE & TEMPLATES):\n%s\n", resp)
			}
		}
		if ragData != "" {
			fmt.Printf("📖 Retrieved %d characters of RAG context.\n", len(ragData))
			if len(ragData) > 100 {
				fmt.Printf("📄 RAG Snippet: %s...\n", ragData[:100])
			}
		} else {
			fmt.Println("⚠️ No RAG context retrieved. Ensure you have uploaded the pine_v6_reference.md to Onyx.")
		}

		// --- Stage 2: Load Local Ground Truth (Bible & Templates) ---
		var localContext string
		projectRoot := findProjectRoot()
		biblePath := filepath.Join(projectRoot, "documents/quant/pine_v6_reference.md")
		templatePath := filepath.Join(projectRoot, "documents/quant/golden_templates.md")
		pitfallsPath := filepath.Join(projectRoot, "documents/quant/pinescript_v6_pitfalls.md")

		if data, err := os.ReadFile(biblePath); err == nil {
			localContext += fmt.Sprintf("\n### PINE SCRIPT V6 BIBLE (GROUND TRUTH):\n%s\n", string(data))
		}
		if data, err := os.ReadFile(templatePath); err == nil {
			localContext += fmt.Sprintf("\n### GOLDEN TEMPLATES (EXAMPLES):\n%s\n", string(data))
		}

		marketPromptData := marketData
		if quantDistill && analystInsight != "" {
			marketPromptData = "(Raw data distilled into Analyst Report below)"
		}

		prompt := fmt.Sprintf(`### DATA SAMPLE (MANDATORY):
%s

### ANALYST REPORT:
%s

### ANALYST CRITIQUE (MANUAL AUDIT):
%s

### DOCUMENTATION CONTEXT (RAG):
%s
%s

### MANDATORY RULES (PHASE 6 HARDENING):
You are a God-tier Pine Script v6 expert. You MUST follow these structural rules:

1. BOILERPLATE: Always start with '//@version=6' and a 'strategy()' header.
2. PRE-CALCULATION (CRITICAL): ALL functions in the 'ta.' and 'math.' namespaces MUST be calculated as variables at the top of the script (Level 0).
   - NEVER call ta.* inside 'if', 'for', or complex logical expressions (e.g., cond1 and ta.rsi(...) > 70).
3. NAMESPACES: Mandatory 'ta.', 'request.', 'math.', 'strategy.', 'input.'.
4. REGIME-BASED DECISION TREE (GATING):
   - **MANDATORY**: Implement logic branching based on the Analyst's 'market_regime'.
   - **IF TRENDING**: Assign high weight (70%%) to the Analyst's Meta-Score and low weight (30%%) to technical indicators. Focus on trend-following entries.
   - **IF RANGING**: Assign low weight (30%%) to the Analyst's Meta-Score and high weight (70%%) to technical oscillators (RSI/Stoch). Require stricter confirmation for entries.
5. FEATURE ENGINEERING (ADVANCED):
   - Calculate 'market_structure' (ADX), 'momentum_bias' (Bias from 1D MA), and 'volatility_expansion' (BBWidth) as Level 0 variables.
   - Use these features to gate or scale your entry signals.
6. RISK MANAGEMENT (REGIME-ADAPTIVE):
   - Use wider stops in TRENDING regimes and tighter, faster trailing stops in RANGING regimes.
7. REASONING:
   - Include brief comments explaining how the Decision Tree is switching the strategy behavior.

USER LOGIC TO IMPLEMENT: %s.
Output ONLY raw code starting with '//@version=6'. No markdown fences. Include a brief comment at the top explaining how to debug if no trades appear using 'plot()'.`, marketPromptData, analystInsight, critiqueData, ragData, localContext, quantLogic)

		if quantPromptOnly {
			promptFile := quantOutput
			// If it's the default pine path or just ends in .pine, switch to .txt for clarity
			if strings.HasSuffix(promptFile, ".pine") {
				promptFile = strings.TrimSuffix(promptFile, ".pine") + ".txt"
			}

			if err := os.WriteFile(promptFile, []byte(prompt), 0644); err != nil {
				return fmt.Errorf("failed to save prompt file: %w", err)
			}
			absPrompt, _ := filepath.Abs(promptFile)
			fmt.Printf("\n📝 Cloud Collaborator Mode: Prompt generated!\n📍 Saved to: %s\n👉 Copy the content and paste it to Gemini to generate your strategy.\n", absPrompt)
			return nil
		}

		model := config.AppConfig.Quant.CoderModel
		if model == "" {
			model = config.AppConfig.Ollama.Model
		}

		fmt.Printf("🤖 Calling Ollama (%s) to generate strategy...\n", model)

		client := api.NewOllamaClient(config.AppConfig.Ollama.BaseURL)
		resp, err := client.Generate(api.GenerateRequest{
			Model:  model,
			Prompt: prompt,
			Stream: false,
		})
		if err != nil {
			return fmt.Errorf("ollama generation failed: %w", err)
		}

		cleanedCode := cleanGeneratedCode(resp.Response, quantLogic)

		// --- Phase 5: Self-Correction Loop ---
		if quantSelfCorrect {
			fmt.Printf("🔍 Stage 3: Self-Correction pass with %s...\n", analystModel)

			var pitfalls string
			if data, err := os.ReadFile(pitfallsPath); err == nil {
				pitfalls = string(data)
			}

			critiquePrompt := fmt.Sprintf(`### GENERATED CODE:
%s

### TARGET LOGIC:
%s

### PINE V6 PITFALLS & RULES:
%s

### TASK:
Critique the code above against the Pine Script v6 rules. CHECK FOR:
1. Are all tuples (MACD, BB, DMI) enclosed in [square brackets]?
2. Are ta.* functions called outside IF/FOR blocks?
3. Is 'strategy.exit' using ticks for profit/loss?
4. Is 'trail_offset' accompanied by 'trail_price'?
5. Are there any hallucinations like 'ta.volume()' or 'security()'?

If there are errors, explain them briefly. If the code is perfect, say "PERFECT".`, cleanedCode, quantLogic, pitfalls)

			critiqueResp, err := client.Generate(api.GenerateRequest{
				Model:  analystModel,
				Prompt: critiquePrompt,
				Stream: false,
			})
			if err == nil && !strings.Contains(critiqueResp.Response, "PERFECT") {
				fmt.Printf("🩹 Refinement needed. Regenerating with critique...\n")

				refinementPrompt := fmt.Sprintf(`### INITIAL CODE:
%s

### ANALYST CRITIQUE:
%s

### MANDATORY RULES:
Re-generate the Pine Script v6 strategy fixing ALL errors mentioned above.
Output ONLY raw code starting with '//@version=6'. No markdown fences.`, cleanedCode, critiqueResp.Response)

				refinementResp, err := client.Generate(api.GenerateRequest{
					Model:  model,
					Prompt: refinementPrompt,
					Stream: false,
				})
				if err == nil {
					cleanedCode = cleanGeneratedCode(refinementResp.Response, quantLogic)
				}
			}
		}

		// 4. Post-processing to fix complex hallucinations
		// Use regex for nested or parameterized ta.volume hallucinations
		reVolFunc := regexp.MustCompile(`ta\.volume\s*\([^)]*\)`)
		cleanedCode = reVolFunc.ReplaceAllString(cleanedCode, "volume")

		reVolAttr := regexp.MustCompile(`ta\.volume`)
		cleanedCode = reVolAttr.ReplaceAllString(cleanedCode, "volume")

		// 4.1. Fix ta.fibonacci() hallucination (Issue #35)
		reFibFunc := regexp.MustCompile(`(?i)ta\.fibonacci\s*\([^)]*\)`)
		cleanedCode = reFibFunc.ReplaceAllString(cleanedCode, "na // ta.fibonacci is a hallucination, use manual calculation")

		// Fix common function name hallucinations
		cleanedCode = strings.ReplaceAll(cleanedCode, "ta.average(", "ta.sma(")
		cleanedCode = strings.ReplaceAll(cleanedCode, "average(", "ta.sma(")

		// Map simple namespace hallucinations
		cleanedCode = strings.ReplaceAll(cleanedCode, "ta.close()", "close")
		cleanedCode = strings.ReplaceAll(cleanedCode, "ta.high()", "high")
		cleanedCode = strings.ReplaceAll(cleanedCode, "ta.low()", "low")
		cleanedCode = strings.ReplaceAll(cleanedCode, "ta.open()", "open")

		// Fix deprecated v5 functions
		cleanedCode = strings.ReplaceAll(cleanedCode, "security(", "request.security(")

		// Fix variable names starting with numbers (e.g., 4HStoc -> h4Stoc, 1hMA -> h1MA)
		varPattern := regexp.MustCompile(`(\s|=)([0-9]+)([HhDdMmWw])([A-Z][a-zA-Z0-9]*)`)
		cleanedCode = varPattern.ReplaceAllString(cleanedCode, `${1}${3}${2}${4}`)

		// 5. Eradicate curly braces and other language keywords
		// Pine Script uses indentation, not braces or then/endif
		cleanedCode = strings.ReplaceAll(cleanedCode, "{", "")
		cleanedCode = strings.ReplaceAll(cleanedCode, "}", "")
		cleanedCode = strings.ReplaceAll(cleanedCode, " then\n", "\n")
		cleanedCode = strings.ReplaceAll(cleanedCode, " then ", " ")
		cleanedCode = strings.ReplaceAll(cleanedCode, "endif", "")

		// 6. Fix invalid type keyword
		cleanedCode = strings.ReplaceAll(cleanedCode, "typ float", "float")
		cleanedCode = strings.ReplaceAll(cleanedCode, "typ int", "int")
		cleanedCode = strings.ReplaceAll(cleanedCode, "typ bool", "bool")
		cleanedCode = strings.ReplaceAll(cleanedCode, "typ string", "string")

		// 7. Fix logical operators (C-style to Pine Script)
		cleanedCode = strings.ReplaceAll(cleanedCode, " && ", " and ")
		cleanedCode = strings.ReplaceAll(cleanedCode, " || ", " or ")

		// 7.5. Fix ambiguous `not` operator patterns (Issue #17)
		// Pattern: "not strategy.position_size > 0" -> "strategy.position_size == 0"
		// Pattern: "not strategy.position_size < 0" -> "strategy.position_size >= 0"
		reNotGreater := regexp.MustCompile(`\bnot\s+(\w+(?:\.\w+)?)\s*>\s*0\b`)
		cleanedCode = reNotGreater.ReplaceAllString(cleanedCode, "${1} == 0")

		reNotLess := regexp.MustCompile(`\bnot\s+(\w+(?:\.\w+)?)\s*<\s*0\b`)
		cleanedCode = reNotLess.ReplaceAllString(cleanedCode, "${1} >= 0")

		// 7.6. Fix ta.atr() parameter hallucination (Issue #18)
		// Pattern: "ta.atr(close, 14)" -> "ta.atr(14)"
		// ATR only accepts length parameter, automatically uses high, low, close
		reAtrParams := regexp.MustCompile(`ta\.atr\s*\(\s*(?:close|high|low|open)\s*,\s*(\d+)\s*\)`)
		cleanedCode = reAtrParams.ReplaceAllString(cleanedCode, "ta.atr($1)")

		// 7.7. Fix request.request.security hallucination
		cleanedCode = strings.ReplaceAll(cleanedCode, "request.request.security", "request.security")

		// 7.8. Fix missing tuple brackets (Issue #19)
		// Pattern: "a, b = c" -> "[a, b] = c"
		reTuple := regexp.MustCompile(`(?m)^(\s*)([a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)+)\s*(:?=)`)
		cleanedCode = reTuple.ReplaceAllString(cleanedCode, "${1}[${2}] ${3}")

		// 7.9. Fix ta.adx() hallucination (Issue #21)
		// Pattern: "adxVal = ta.adx(14)" -> "[_, _, adxVal] = ta.dmi(14, 14)"
		reAdx := regexp.MustCompile(`(\w+)\s*=\s*ta\.adx\s*\(\s*(\d+)\s*\)`)
		cleanedCode = reAdx.ReplaceAllString(cleanedCode, "[_, _, ${1}] = ta.dmi(${2}, ${2})")

		// 7.10. Fix ta.dmi() parameter count (Issue #22)
		// Pattern: "ta.dmi(14)" -> "ta.dmi(14, 14)"
		reDmiParams := regexp.MustCompile(`ta\.dmi\s*\(\s*(\d+)\s*\)`)
		cleanedCode = reDmiParams.ReplaceAllString(cleanedCode, "ta.dmi(${1}, ${1})")

		// 7.11. Fix "for X bars" natural language hallucination (Issue #22)
		// Pattern: "cond = expr for 3 bars" -> "cond = ta.all(expr, 3)"
		reForBars := regexp.MustCompile(`(?m)^(\s*)(\w+)\s*=\s*(.*?)\s+for\s+(\d+)\s+bars(?:\s*//.*)?\s*$`)
		cleanedCode = reForBars.ReplaceAllString(cleanedCode, "${1}${2} = ta.all(${3}, ${4})")

		// 7.12. Fix DMI variable order hallucination (Issue #22 extension)
		// Pattern: "[adx, diPlus, diMinus] = ta.dmi" -> "[diPlus, diMinus, adx] = ta.dmi"
		reDmiOrder := regexp.MustCompile(`\[\s*(\w*adx\w*)\s*,\s*(\w+)\s*,\s*(\w+)\s*\]\s*(:?=)\s*ta\.dmi`)
		cleanedCode = reDmiOrder.ReplaceAllString(cleanedCode, "[${2}, ${3}, ${1}] ${4} ta.dmi")

		// 7.13. Fix direct na comparisons (Issue #23)
		// Pattern: "val != na" -> "not na(val)"
		reNotNa := regexp.MustCompile(`(\w+(?:\.\w+)?)\s*!=\s*na`)
		cleanedCode = reNotNa.ReplaceAllString(cleanedCode, "not na(${1})")
		// Pattern: "val == na" -> "na(val)"
		reIsNa := regexp.MustCompile(`(\w+(?:\.\w+)?)\s*==\s*na`)
		cleanedCode = reIsNa.ReplaceAllString(cleanedCode, "na(${1})")

		// 7.14. Fix timed exit hallucination (Issue #24)
		// Pattern: "strategy.closedtrades.exit_bar(...) == bar_index + 5" -> "bar_index - strategy.opentrades.entry_bar_index(0) >= 5"
		reTimedExit := regexp.MustCompile(`strategy\.closedtrades\.exit_bar\(.*?\)\s*==\s*bar_index\s*\+\s*(\d+)`)
		cleanedCode = reTimedExit.ReplaceAllString(cleanedCode, "bar_index - strategy.opentrades.entry_bar_index(0) >= ${1}")
		// Generic cleanup for any remaining exit_bar calls
		cleanedCode = strings.ReplaceAll(cleanedCode, "strategy.closedtrades.exit_bar", "strategy.opentrades.entry_bar_index")

		// 7.15. Fix Bollinger Bands tuple size mismatch (Issue #25)
		// Pattern: "[upper, lower] = ta.bb" -> "[_, upper, lower] = ta.bb"
		// Only fixes cases where exactly two variables are provided to ta.bb
		reBbTuple := regexp.MustCompile(`\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*(:?=)\s*ta\.bb`)
		cleanedCode = reBbTuple.ReplaceAllString(cleanedCode, "[_, ${1}, ${2}] ${3} ta.bb")

		// 7.22. Fix MACD tuple size mismatch (Issue #37)
		// Pattern: "[macd, signal] = ta.macd" -> "[macd, signal, _] = ta.macd"
		reMacdTuple := regexp.MustCompile(`\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*(:?=)\s*ta\.macd`)
		cleanedCode = reMacdTuple.ReplaceAllString(cleanedCode, "[${1}, ${2}, _] ${3} ta.macd")

		// 7.23. Fix DMI tuple size mismatch (Issue #38)
		// Pattern: "[diPlus, diMinus] = ta.dmi" -> "[diPlus, diMinus, _] = ta.dmi"
		reDmiTuple := regexp.MustCompile(`\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*(:?=)\s*ta\.dmi`)
		cleanedCode = reDmiTuple.ReplaceAllString(cleanedCode, "[${1}, ${2}, _] ${3} ta.dmi")

		// 7.24. Fix single variable MACD assignment (Issue #39)
		// Pattern: "macdLine = ta.macd(" -> "[macdLine, _, _] = ta.macd("
		reMacdSingle := regexp.MustCompile(`(?m)^(\s*)(\w+)\s*(:?=)\s*ta\.macd\s*\(`)
		cleanedCode = reMacdSingle.ReplaceAllString(cleanedCode, "${1}[${2}, _, _] ${3} ta.macd(")

		// 7.16. Fix missing ta. namespace for common functions (Issue #26)
		taFuncs := []string{
			"barssince", "valuewhen", "pivothigh", "pivotlow", "highest", "lowest",
			"sma", "ema", "rsi", "macd", "atr", "stoch", "bb", "dmi", "stdev",
			"change", "cross", "crossover", "crossunder", "rising", "falling",
			"all", "any", "percentrank", "vwap", "wma", "rma", "tr", "dev",
		}
		for _, fn := range taFuncs {
			re := regexp.MustCompile(`(?m)(^|[^a-zA-Z0-9._])\b(` + fn + `)\s*\(`)
			cleanedCode = re.ReplaceAllString(cleanedCode, "${1}ta.${2}(")
		}

		// 7.17. Fix line continuation syntax error (Issue #28)
		// Pattern: "cond1 and \n    cond2" -> "cond1 and cond2"
		// Only joins lines ending with 'and' or 'or' (common logical split points)
		reLineCont := regexp.MustCompile(`\b(and|or)\s*\n\s+`)
		cleanedCode = reLineCont.ReplaceAllString(cleanedCode, "${1} ")

		// 7.18. Fix ta.vwma/vwap confusion (Issue #29)
		// Pattern: "vwap = ta.vwma(close, 14)" -> "vwap = ta.vwap(close)"
		// If the variable name is 'vwap' but the function is 'vwma', it's almost certainly a mistake.
		reVwapMatch := regexp.MustCompile(`(\bvwap\b\s*=\s*)ta\.vwma\s*\(\s*([^,]+)\s*,\s*\d+\s*\)`)
		cleanedCode = reVwapMatch.ReplaceAllString(cleanedCode, "${1}ta.vwap(${2})")

		// 7.19. Fix ta.valuewhen(src, n) hallucination (Issue #30)
		// Pattern: "ta.valuewhen(close, 1)" -> "close[1]"
		// This regex targets cases where only a source and a number are provided (wrong API usage)
		reValuewhenHistory := regexp.MustCompile(`ta\.valuewhen\s*\(\s*(\w+(?:\.\w+)?)\s*,\s*(\d+)\s*\)`)
		cleanedCode = reValuewhenHistory.ReplaceAllString(cleanedCode, "${1}[${2}]")

		// 7.20. Fix missing request. namespace for security (Issue #31)
		// Pattern: "security(" or ".security(" -> "request.security("
		reSecurityPrefix := regexp.MustCompile(`(^|[^a-zA-Z0-9_])(?i:security|request\.security)\s*\(`)
		cleanedCode = reSecurityPrefix.ReplaceAllString(cleanedCode, "${1}request.security(")
		// 7.21. Fix strategy.exit missing trail_offset hallucination (Issue #36)
		// Catch strategy.exit calls that have a trail_price but no trail_offset or other exit parameters
		reExitMissingOffset := regexp.MustCompile(`strategy\.exit\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*trail_price\s*=[^,)]+\s*\)`)
		cleanedCode = reExitMissingOffset.ReplaceAllString(cleanedCode, "strategy.exit($1, $2, trail_price=close, trail_offset=500) // WARNING: Offset was missing, using 500 ticks default")

		// 7.21. Fix double request namespace hallucination (Issue #19 / #31 extension)
		// Pattern: "request.request.security(" -> "request.security("
		reDoubleRequest := regexp.MustCompile(`request\.request\.security\s*\(`)
		cleanedCode = reDoubleRequest.ReplaceAllString(cleanedCode, "request.security(")

		// 7.21. Cleanup natural language fragments and isolated operators (Issue #32)
		// Removes lines that are just numbers, single words, or isolated operators (common LLM artifacts)
		lines := strings.Split(cleanedCode, "\n")
		var filteredLines []string
		for _, line := range lines {
			trimmed := strings.TrimSpace(line)
			// Skip lines that are just a number, an isolated operator, or a very short word without assignments
			if trimmed == "" {
				filteredLines = append(filteredLines, line)
				continue
			}
			isFragment := false
			// Pattern: just a number or an isolated operator like "* atr" or "0 ="
			reFragment := regexp.MustCompile(`^([\d.]+|[\+\-\*/=\s]+|[\w]{1,3})$`)
			if reFragment.MatchString(trimmed) && !strings.Contains(trimmed, "(") {
				isFragment = true
			}
			// Special case for fragments seen in screenshot: "* atr", "ls", "atr"
			if trimmed == "* atr" || trimmed == "atr" || trimmed == "ls" || trimmed == "lose, 14)" {
				isFragment = true
			}
			if !isFragment {
				filteredLines = append(filteredLines, line)
			}
		}
		cleanedCode = strings.Join(filteredLines, "\n")

		// 7.22. Fix strategy variables inside request.security (Issue #33)
		// Pattern: "request.security(..., strategy.anything)" -> "strategy.anything"
		reStrategyInSecurity := regexp.MustCompile(`request\.security\s*\(\s*[^,]+\s*,\s*[^,]+\s*,\s*(strategy\.\w+)\s*\)`)
		cleanedCode = reStrategyInSecurity.ReplaceAllString(cleanedCode, "${1}")

		// 8. Ensure strategy() header exists

		if !strings.Contains(cleanedCode, "strategy(") {
			headerName := quantLogic
			if len(headerName) > 50 {
				headerName = headerName[:47] + "..."
			}
			header := fmt.Sprintf("strategy(\"%s\", overlay=true)\n", headerName)
			// Insert after version tag
			lines := strings.Split(cleanedCode, "\n")
			if len(lines) > 0 && strings.HasPrefix(lines[0], "//@version") {
				cleanedCode = lines[0] + "\n" + header + strings.Join(lines[1:], "\n")
			} else {
				cleanedCode = "//@version=6\n" + header + "\n" + cleanedCode
			}
		}

		code := strings.TrimSpace(cleanedCode)

		if quantOutput == "" {
			quantOutput = "strategy.pine"
		}

		err = os.WriteFile(quantOutput, []byte(code), 0644)
		if err != nil {
			return fmt.Errorf("failed to write output file: %w", err)
		}

		absOutput, _ := filepath.Abs(quantOutput)
		fmt.Printf("\n🎉 Strategy generated successfully!\n📍 Saved to: %s\n", absOutput)
		fmt.Println("\n👉 NEXT STEP: Open TradingView > Pine Editor > Paste this code > Save > Add to Chart.")

		return nil
	},
}

// analyzeMarketData uses the analyst model (Plutus) to provide market insights
func analyzeMarketData(allData []TimeframeData, strategyLogic string) (string, error) {
	// Build market summary for analyst
	var dataDesc strings.Builder
	for _, data := range allData {
		dataDesc.WriteString(fmt.Sprintf("\n=== %s Timeframe (%s) ===\n", data.Timeframe, data.Filename))
		dataDesc.WriteString(api.FormatCandlesForLLM(data.Candles))
	}

	// Construct analyst prompt
	analystPrompt := fmt.Sprintf(`You are a professional quantitative analyst specializing in cryptocurrency trading strategies.

MARKET DATA:
%s

USER'S STRATEGY IDEA:
%s

TASK:
### ANALYST TASK: META-LEARNER & FEATURE TAGGING
1. **FEATURE TAGGING**: Analyze and report these technical features:
   - **Market Structure**: "TRENDING" (ADX > 25) vs "RANGING" (ADX <= 25).
   - **Momentum Bias**: Calculate the deviation of current 1H price from the 1D Moving Average.
   - **Volatility Expansion**: Report the Bollinger Bandwidth (upper-lower)/basis.
2. **META-LEARNER ANALYSIS**:
   - Act as a **Meta-Learner**. Combine multi-timeframe indicators, volume profile, and current volatility.
   - Output a **Meta-Score** (-100 to 100) where -100 is absolute bearish conviction and 100 is absolute bullish conviction.
3. **STRATEGY RECOMMENDATIONS (REGIME-ADAPTIVE)**:
   - Provide separate entry/exit rules for TRENDING vs RANGING states.
   - If TRENDING: Focus on pullback entries and trend extensions.
   - If RANGING: Focus on mean reversion and overbought/oversold boundaries.

4. Provide a structured **META-ANALYSIS SCORE** in a JSON block (REQUIRED) at the end:
   {
     "timeframes": {
       "1D": {"trend": "Bullish", "strength": 85, "confidence": 90},
       "4H": {"trend": "Neutral", "strength": 40, "confidence": 60},
       "1H": {"trend": "Bullish", "strength": 60, "confidence": 75}
     },
     "market_regime": "TRENDING",
     "volatility_regime": "High",
     "meta_score": 75,
     "features": {
        "adx": 28,
        "bias_pct": 3.5,
        "bb_bandwidth": 0.12
     }
   }

Provide a detailed technical analysis focusing on structural logic for a Decision Tree strategy.`,
		dataDesc.String(),
		strategyLogic,
	)

	// Call Ollama with analyst model
	client := api.NewOllamaClient(config.AppConfig.Ollama.BaseURL)
	model := config.AppConfig.Quant.AnalystModel
	if model == "" {
		model = "deepseek-r1:32b"
	}

	req := api.GenerateRequest{
		Model:  model,
		Prompt: analystPrompt,
		Stream: false,
	}

	response, err := client.Generate(req)
	if err != nil {
		return "", fmt.Errorf("analyst model failed: %w", err)
	}

	return response.Response, nil
}

// detectTimeframe extracts timeframe from filename pattern and returns name and minutes
func detectTimeframe(filename string) (string, int) {
	base := filepath.Base(filename)
	lower := strings.ToLower(base)

	type tfInfo struct {
		name    string
		minutes int
	}

	patterns := map[string]tfInfo{
		"_1m.csv":  {"1M", 1},
		"_5m.csv":  {"5M", 5},
		"_15m.csv": {"15M", 15},
		"_30m.csv": {"30M", 30},
		"_1h.csv":  {"1H", 60},
		"_2h.csv":  {"2H", 120},
		"_4h.csv":  {"4H", 240},
		"_1d.csv":  {"1D", 1440},
		"_1w.csv":  {"1W", 10080},
	}

	for pattern, info := range patterns {
		if strings.Contains(lower, pattern) {
			return info.name, info.minutes
		}
	}
	return "Unknown", 0
}

// formatMultiTimeframeData formats multiple timeframe datasets for LLM prompt
func formatMultiTimeframeData(allData []TimeframeData) string {
	var sb strings.Builder

	for _, data := range allData {
		sb.WriteString(fmt.Sprintf("\n=== TIMEFRAME: %s (%s) ===\n", data.Timeframe, data.Filename))
		sb.WriteString(api.FormatCandlesForLLM(data.Candles))
		sb.WriteString("\n")
	}

	sb.WriteString("\n📊 MULTI-TIMEFRAME STRATEGY REQUIREMENTS:\n")
	sb.WriteString("1. Use request.security() to fetch higher timeframe data\n")
	sb.WriteString("2. Example MTF pattern:\n")
	sb.WriteString("   dailyTrend = request.security(syminfo.tickerid, \"D\", ta.sma(close, 50))\n")
	sb.WriteString("   hourlySignal = ta.crossover(fast, slow)\n")
	sb.WriteString("   if dailyTrend > dailyTrend[1] and hourlySignal\n")
	sb.WriteString("       strategy.entry(\"Long\", strategy.long)\n")
	sb.WriteString("3. Always validate higher timeframe BEFORE lower timeframe signals\n")
	sb.WriteString("4. Document which timeframe is used for trend vs. entry\n")

	return sb.String()
}

// findProjectRoot attempts to find the root of the project by looking for go.mod or .git
func findProjectRoot() string {
	cwd, _ := os.Getwd()
	dir := cwd
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		if _, err := os.Stat(filepath.Join(dir, ".git")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return cwd // fallback
		}
		dir = parent
	}
}

func init() {
	quantCmd.AddCommand(genCmd)

	genCmd.Flags().StringArrayVarP(&quantInputs, "input", "i", []string{}, "Path(s) to TradingView CSV file(s) (required, can be specified multiple times for MTF analysis)")
	genCmd.Flags().StringVarP(&quantOutput, "output", "o", "strategy.pine", "Path to save the generated script")
	genCmd.Flags().StringVarP(&quantLogic, "logic", "l", "simple moving average cross", "The trading logic/strategy description")
	genCmd.Flags().IntVar(&quantLimit, "limit", 50, "Number of recent candles to provide as context")
	genCmd.Flags().StringVar(&quantCritique, "critique", "", "Optional path to an analyst audit report for refinement")
	genCmd.Flags().StringVar(&quantRAG, "rag", "", "Override the AnythingLLM RAG workspace name")
	genCmd.Flags().StringVar(&quantRAGProv, "rag-provider", "", "Override the RAG provider (anything or onyx)")
	genCmd.Flags().IntVar(&onyxProjectID, "onyx-project-id", 0, "Override the Onyx Project ID")
	genCmd.Flags().BoolVar(&quantUseAnalyst, "use-analyst", false, "Enable two-stage workflow: market analysis with Plutus, then code generation")
	genCmd.Flags().StringVar(&quantSaveAnalysis, "save-analysis", "", "Save market analysis to file (for debugging, requires --use-analyst)")
	genCmd.Flags().BoolVar(&quantForceMaxAlign, "force-max-alignment", false, "Synchronize all timeframes to the highest timeframe's window (Caution: increases context size exponentially)")
	genCmd.Flags().BoolVar(&quantSelfCorrect, "self-correct", true, "Automatically critique and refine generated code (Bible mode)")
	genCmd.Flags().BoolVar(&quantDistill, "distill", false, "Distilled reasoning mode: Omit raw data from coder prompt when using analyst")
	genCmd.Flags().BoolVar(&quantPromptOnly, "prompt-only", false, "Cloud Collaborator Mode: Generate a comprehensive prompt for Gemini and exit")

	genCmd.MarkFlagRequired("input")

	// Register completion for the --logic flag
	genCmd.RegisterFlagCompletionFunc("logic", func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
		return config.AppConfig.Quant.Logics, cobra.ShellCompDirectiveNoFileComp
	})
}

// Helper to clean generated code
func cleanGeneratedCode(rawCode, quantLogic string) string {
	cleanedCode := rawCode

	// 1. Attempt to extract from JSON if detected anywhere
	if strings.Contains(rawCode, "\"code\"") {
		startIdx := strings.Index(rawCode, "{")
		endIdx := strings.LastIndex(rawCode, "}")
		if startIdx != -1 && endIdx != -1 && endIdx > startIdx {
			jsonStr := rawCode[startIdx : endIdx+1]
			var data map[string]interface{}
			if err := json.Unmarshal([]byte(jsonStr), &data); err == nil {
				if codeVal, ok := data["code"].(string); ok {
					cleanedCode = codeVal
				}
			}
		}
	}

	// 2. Discard everything before //@version=6 (strips preambles)
	versionIdx := strings.Index(cleanedCode, "//@version=6")
	if versionIdx != -1 {
		cleanedCode = cleanedCode[versionIdx:]
	}

	// 3. Handle Markdown blocks (if version tag wasn't first)
	firstFence := strings.Index(cleanedCode, "```")
	lastFence := strings.LastIndex(cleanedCode, "```")

	if firstFence != -1 && lastFence != -1 && firstFence != lastFence {
		cleanedCode = cleanedCode[firstFence+3 : lastFence]
		// Remove language tag
		lines := strings.Split(cleanedCode, "\n")
		if len(lines) > 0 {
			tag := strings.TrimSpace(lines[0])
			if tag == "pine" || tag == "pinescript" {
				cleanedCode = strings.Join(lines[1:], "\n")
			}
		}
	}
	return cleanedCode
}
