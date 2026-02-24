package api

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

type ForgeClient struct {
	BaseURL string
	HTTP    *http.Client
}

func NewForgeClient(baseURL string) *ForgeClient {
	return &ForgeClient{
		BaseURL: baseURL,
		HTTP: &http.Client{
			Timeout: 300 * time.Second,
		},
	}
}

type Txt2ImgRequest struct {
	Prompt           string                 `json:"prompt"`
	NegativePrompt   string                 `json:"negative_prompt"`
	Steps            int                    `json:"steps"`
	Width            int                    `json:"width"`
	Height           int                    `json:"height"`
	CFGScale         float64                `json:"cfg_scale"`
	SamplerName      string                 `json:"sampler_name"`
	OverrideSettings map[string]interface{} `json:"override_settings"`
}

type Txt2ImgResponse struct {
	Images []string `json:"images"`
}

type TaggerRequest struct {
	Image string  `json:"image"`
	Model string  `json:"model"`
	Threshold float64 `json:"threshold"`
}

type TaggerResponse struct {
	Caption map[string]float64 `json:"caption"`
}

func (c *ForgeClient) TagImage(req TaggerRequest) (map[string]float64, error) {
	url := fmt.Sprintf("%s/tagger/v1/interrogate", c.BaseURL)
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
		return nil, fmt.Errorf("forge tagger error (status %d): %s", res.StatusCode, string(body))
	}

	var resp TaggerResponse
	if err := json.NewDecoder(res.Body).Decode(&resp); err != nil {
		return nil, err
	}

	return resp.Caption, nil
}

func (c *ForgeClient) Txt2Img(req Txt2ImgRequest, outputPath string) error {
	url := fmt.Sprintf("%s/sdapi/v1/txt2img", c.BaseURL)
	payload, err := json.Marshal(req)
	if err != nil {
		return err
	}

	res, err := c.HTTP.Post(url, "application/json", bytes.NewBuffer(payload))
	if err != nil {
		return err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(res.Body)
		return fmt.Errorf("forge error (status %d): %s", res.StatusCode, string(body))
	}

	var resp Txt2ImgResponse
	if err := json.NewDecoder(res.Body).Decode(&resp); err != nil {
		return err
	}

	if len(resp.Images) == 0 {
		return fmt.Errorf("no images returned from forge")
	}

	// Decode first image
	imgData, err := base64.StdEncoding.DecodeString(resp.Images[0])
	if err != nil {
		return fmt.Errorf("failed to decode base64 image: %w", err)
	}

	// Ensure directory exists
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return err
	}

	return os.WriteFile(outputPath, imgData, 0644)
}
