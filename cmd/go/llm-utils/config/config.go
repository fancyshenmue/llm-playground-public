package config

import (
	"fmt"
	"strings"

	"github.com/spf13/viper"
)

// Config holds all the configuration for the application
type Config struct {
	Ollama   OllamaConfig `mapstructure:"ollama"`
	Forge    ForgeConfig  `mapstructure:"forge"`
	Anything AnythingLLM  `mapstructure:"anythingllm"`
	Onyx     OnyxConfig   `mapstructure:"onyx"`
	Kohya    KohyaConfig  `mapstructure:"kohya"`
	Quant    QuantConfig  `mapstructure:"quant"`
}

type QuantConfig struct {
	Logics       []string `mapstructure:"logics"`
	AnalystModel string   `mapstructure:"analyst_model"`
	CoderModel   string   `mapstructure:"coder_model"`
	RAGWorkspace string   `mapstructure:"rag_workspace"`
	RAGProvider  string   `mapstructure:"rag_provider"` // "anything" or "onyx"
}

type OllamaConfig struct {
	BaseURL string `mapstructure:"api_url"`
	Model   string `mapstructure:"vision_model"`
}

type ForgeConfig struct {
	BaseURL string   `mapstructure:"api_url"`
	Model   string   `mapstructure:"base_model"`
	Loras   []string `mapstructure:"loras"`
}

type AnythingLLM struct {
	BaseURL   string `mapstructure:"api_url"`
	APIKey    string `mapstructure:"api_key"`
	Workspace string `mapstructure:"workspace_slug"`
}

type OnyxConfig struct {
	BaseURL   string `mapstructure:"api_url"`
	APIKey    string `mapstructure:"api_key"`
	PersonaID int    `mapstructure:"persona_id"`
	ProjectID int    `mapstructure:"project_id"`
}

type KohyaConfig struct {
	RootPath      string `mapstructure:"root_path"`
	VenvPath      string `mapstructure:"venv_path"`
	DefaultConfig string `mapstructure:"default_config"`
}

var AppConfig Config

// InitConfig initializes the configuration using Viper
func InitConfig(cfgFile string) error {
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		viper.AddConfigPath(".")
		viper.AddConfigPath("./cmd/go/llm-utils")
		viper.SetConfigName("config")
		viper.SetConfigType("yaml")
	}

	viper.SetEnvPrefix("LLM")
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	viper.AutomaticEnv()

	// Set defaults
	viper.SetDefault("ollama.api_url", "http://localhost:11434/api")
	viper.SetDefault("ollama.vision_model", "llama3.2-vision")
	viper.SetDefault("forge.api_url", "http://127.0.0.1:7861/sdapi/v1")
	viper.SetDefault("forge.base_model", "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors")
	viper.SetDefault("quant.rag_provider", "anything")
	viper.SetDefault("onyx.api_url", "http://localhost:3000")
	viper.SetDefault("onyx.persona_id", 0)
	viper.SetDefault("onyx.project_id", 0)

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return fmt.Errorf("error reading config file: %w", err)
		}
		// Config file not found is okay, we use defaults or env vars
	}

	if err := viper.Unmarshal(&AppConfig); err != nil {
		return fmt.Errorf("unable to decode into struct: %w", err)
	}

	return nil
}
