package cmd

import (
	"fmt"
	"os"

	"llm-playground/cmd/go/llm-utils/config"
	"llm-playground/internal/go/api"

	"github.com/spf13/cobra"
)

var (
	auditInput  string
	auditCtx    string
	auditTrades string
	auditOutput string
)

var auditCmd = &cobra.Command{
	Use:   "audit",
	Short: "Audit a Pine Script strategy using an AI Analyst",
	Long: `Passes a generated Pine Script strategy to a specialized 'Analyst' model
(e.g., Plutus) to identify logical flaws, risk management issues, or overfitting.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// 1. Read the script
		script, err := os.ReadFile(auditInput)
		if err != nil {
			return fmt.Errorf("failed to read script: %w", err)
		}

		// 2. Read context if available
		var ctxData string
		if auditCtx != "" {
			candles, err := api.ParseTradingViewCSV(auditCtx, 20)
			if err == nil {
				ctxData = api.FormatCandlesForLLM(candles)
			}
		}

		// 3. Read trades if available
		var tradeData string
		if auditTrades != "" {
			trades, err := api.ParseTradeListCSV(auditTrades)
			if err == nil {
				tradeData = api.FormatTradesForLLM(trades)
			}
		}

		prompt := fmt.Sprintf(`You are a Senior Quantitative Analyst.
Audit the following TradingView Pine Script strategy.

STRATEGY CODE:
%s

MARKET CONTEXT (Last 20 Candles):
%s

BACKTEST PERFORMANCE (Trade List):
%s

TASK:
1. Identify logical flaws or code bugs.
2. Evaluate risk management based on real performance (Max Drawdown vs Max RunUp).
3. Cross-reference failed trades with code logic to find the cause.
4. Check for potential overfitting based on market context.
5. Suggest specific refinements to improve robustness.

Output a concise report in Markdown format.`, string(script), ctxData, tradeData)

		model := config.AppConfig.Quant.AnalystModel
		if model == "" {
			model = config.AppConfig.Ollama.Model
		}

		fmt.Printf("🧐 Calling Analyst (%s) to audit strategy...\n", model)

		client := api.NewOllamaClient(config.AppConfig.Ollama.BaseURL)
		resp, err := client.Generate(api.GenerateRequest{
			Model:  model,
			Prompt: prompt,
			Stream: false,
		})
		if err != nil {
			return fmt.Errorf("audit failed: %w", err)
		}

		fmt.Println("\n--- 📊 AI AUDIT REPORT ---")
		fmt.Println(resp.Response)
		fmt.Println("--------------------------")

		if auditOutput != "" {
			err = os.WriteFile(auditOutput, []byte(resp.Response), 0644)
			if err != nil {
				return fmt.Errorf("failed to write audit report: %w", err)
			}
			fmt.Printf("📝 Audit report saved to: %s\n", auditOutput)
		}

		return nil
	},
}

func init() {
	quantCmd.AddCommand(auditCmd)

	auditCmd.Flags().StringVarP(&auditInput, "input", "i", "", "Path to the .pine script to audit (required)")
	auditCmd.Flags().StringVarP(&auditCtx, "context", "c", "", "Path to CSV market data for context")
	auditCmd.Flags().StringVarP(&auditTrades, "trades", "t", "", "Path to CSV Trade List export from strategy report")
	auditCmd.Flags().StringVarP(&auditOutput, "output", "o", "", "Path to save the audit report (optional)")

	auditCmd.MarkFlagRequired("input")
}
