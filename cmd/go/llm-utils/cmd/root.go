package cmd

import (
	"llm-playground/cmd/go/llm-utils/config"

	"github.com/spf13/cobra"
)

var (
	verbose bool
	cfgFile string
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "llm-utils",
	Short: "A CLI tool for testing and interacting with AI model APIs",
	Long: `llm-utils is a multi-purpose CLI designed to help developers 
work with various LLM providers like Ollama, OpenAI, and more.
It supports chat, evaluation, and benchmarking.`,
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		return config.InitConfig(cfgFile)
	},
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() error {
	return rootCmd.Execute()
}

func init() {
	// Persistent flags that are available to every command
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "enable verbose output")
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is ./config.yaml)")

	// Local flags for the root command
	rootCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
