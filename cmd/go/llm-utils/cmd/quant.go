package cmd

import (
	"github.com/spf13/cobra"
)

// quantCmd represents the quant command
var quantCmd = &cobra.Command{
	Use:   "quant",
	Short: "AI-driven financial strategy tools",
	Long: `A collection of tools for fetching market data, generating Pine Script strategies,
and analyzing backtest results using local LLMs.`,
}

func init() {
	rootCmd.AddCommand(quantCmd)
}
