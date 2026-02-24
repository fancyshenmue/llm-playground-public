package cmd

import (
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"llm-playground/internal/go/api"

	"github.com/adshao/go-binance/v2"
	"github.com/spf13/cobra"
)

var (
	fetchSymbol     string
	fetchExchange   string
	fetchTimeframes string
	fetchLimit      int
	fetchOutput     string
	fetchSince      string
)

var quantFetchCmd = &cobra.Command{
	Use:   "fetch",
	Short: "Download multi-timeframe OHLCV data from crypto exchanges",
	Long: `Automatically download historical candlestick data from cryptocurrency exchanges.

Example:
  llm-utils quant fetch --symbol BTCUSDT --timeframes 1h,4h,1d --limit 2000
`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Parse timeframes
		timeframes := strings.Split(fetchTimeframes, ",")

		fmt.Printf("📊 Fetching data for %s from %s exchange\n", fetchSymbol, fetchExchange)
		fmt.Printf("⏱️  Timeframes: %s\n", fetchTimeframes)
		if fetchSince != "" {
			fmt.Printf("📅 Since: %s (pagination enabled)\n", fetchSince)
		} else {
			fmt.Printf("📈 Limit: %d candles per timeframe\n", fetchLimit)
		}
		fmt.Println()

		// Parse since date if provided
		var startTime int64
		if fetchSince != "" {
			t, err := time.Parse("2006-01-02", fetchSince)
			if err != nil {
				return fmt.Errorf("invalid date format for --since (use YYYY-MM-DD): %w", err)
			}
			startTime = t.Unix() * 1000 // Convert to milliseconds
		}

		// Create Binance client
		client := api.NewBinanceClient()

		// Download data for each timeframe
		for _, tf := range timeframes {
			tf = strings.TrimSpace(tf)
			interval := api.TimeframeToInterval(tf)

			fmt.Printf("🔄 Downloading %s data...\n", tf)

			var klines []*binance.Kline
			var err error

			if startTime > 0 {
				// Use pagination to fetch all data from start date
				klines, err = client.FetchAllKlines(fetchSymbol, interval, startTime)
			} else {
				// Use simple limit-based fetch
				klines, err = client.FetchKlines(fetchSymbol, interval, fetchLimit, 0)
			}
			if err != nil {
				return fmt.Errorf("failed to fetch %s data: %w", tf, err)
			}

			// Generate filename
			symbolLower := strings.ToLower(fetchSymbol)
			filename := fmt.Sprintf("%s_%s.csv", symbolLower, tf)
			filepath := filepath.Join(fetchOutput, filename)

			// Save to CSV
			if err := api.SaveKlinesToCSV(klines, filepath); err != nil {
				return fmt.Errorf("failed to save %s data: %w", tf, err)
			}

			fmt.Printf("✅ Saved %d candles to: %s\n\n", len(klines), filepath)
		}

		fmt.Println("🎉 All data downloaded successfully!")
		return nil
	},
}

func init() {
	quantCmd.AddCommand(quantFetchCmd)

	quantFetchCmd.Flags().StringVar(&fetchSymbol, "symbol", "BTCUSDT", "Trading pair symbol (e.g., BTCUSDT, ETHUSDT)")
	quantFetchCmd.Flags().StringVar(&fetchExchange, "exchange", "binance", "Exchange name (currently only binance supported)")
	quantFetchCmd.Flags().StringVar(&fetchTimeframes, "timeframes", "1d", "Comma-separated timeframes (e.g., 1h,4h,1d)")
	quantFetchCmd.Flags().IntVar(&fetchLimit, "limit", 1000, "Maximum number of candles to download per timeframe")
	quantFetchCmd.Flags().StringVar(&fetchOutput, "output", "dataset/trading", "Output directory for CSV files")
	quantFetchCmd.Flags().StringVar(&fetchSince, "since", "", "Start date for historical data (YYYY-MM-DD, enables pagination)")
}
