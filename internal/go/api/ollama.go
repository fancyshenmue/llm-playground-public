package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type OllamaClient struct {
	BaseURL string
	HTTP    *http.Client
}

func NewOllamaClient(baseURL string) *OllamaClient {
	return &OllamaClient{
		BaseURL: baseURL,
		HTTP: &http.Client{
			Timeout: 300 * time.Second,
		},
	}
}

type GenerateRequest struct {
	Model  string   `json:"model"`
	Prompt string   `json:"prompt"`
	Stream bool     `json:"stream"`
	Images []string `json:"images,omitempty"`
	Format string   `json:"format,omitempty"`
}

type GenerateResponse struct {
	Model    string `json:"model"`
	Response string `json:"response"`
	Done     bool   `json:"done"`
}

func (c *OllamaClient) Generate(req GenerateRequest) (*GenerateResponse, error) {
	url := fmt.Sprintf("%s/api/generate", c.BaseURL)
	payload, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	res, err := c.HTTP.Post(url, "application/json", bytes.NewBuffer(payload))
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(res.Body)
		return nil, fmt.Errorf("ollama error (status %d): %s", res.StatusCode, string(body))
	}

	var resp GenerateResponse
	if err := json.NewDecoder(res.Body).Decode(&resp); err != nil {
		return nil, err
	}

	return &resp, nil
}

func (c *OllamaClient) ListModels() ([]string, error) {
	url := fmt.Sprintf("%s/api/tags", c.BaseURL)
	res, err := c.HTTP.Get(url)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	var data struct {
		Models []struct {
			Name string `json:"name"`
		} `json:"models"`
	}

	if err := json.NewDecoder(res.Body).Decode(&data); err != nil {
		return nil, err
	}

	names := make([]string, len(data.Models))
	for i, m := range data.Models {
		names[i] = m.Name
	}
	return names, nil
}
