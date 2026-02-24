package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type AnythingClient struct {
	BaseURL string
	APIKey  string
	HTTP    *http.Client
}

func NewAnythingClient(baseURL, apiKey string) *AnythingClient {
	return &AnythingClient{
		BaseURL: baseURL,
		APIKey:  apiKey,
		HTTP: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

type RawTextRequest struct {
	TextContent string                 `json:"textContent"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type RawTextResponse struct {
	Success   bool `json:"success"`
	Documents []struct {
		Location string `json:"location"`
	} `json:"documents"`
}

func (c *AnythingClient) UploadRawText(req RawTextRequest) (string, error) {
	url := fmt.Sprintf("%s/document/raw-text", c.BaseURL)
	payload, err := json.Marshal(req)
	if err != nil {
		return "", err
	}

	httpReq, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	if err != nil {
		return "", err
	}

	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.APIKey))
	httpReq.Header.Set("Content-Type", "application/json")

	res, err := c.HTTP.Do(httpReq)
	if err != nil {
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(res.Body)
		return "", fmt.Errorf("anythingLLM error (status %d): %s", res.StatusCode, string(body))
	}

	var resp RawTextResponse
	if err := json.NewDecoder(res.Body).Decode(&resp); err != nil {
		return "", err
	}

	if len(resp.Documents) == 0 {
		return "", fmt.Errorf("no documents returned from anythingLLM")
	}

	return resp.Documents[0].Location, nil
}

func (c *AnythingClient) UpdateEmbeddings(workspace string, locations []string) error {
	url := fmt.Sprintf("%s/workspace/%s/update-embeddings", c.BaseURL, workspace)
	payload, err := json.Marshal(map[string]interface{}{
		"adds": locations,
	})
	if err != nil {
		return err
	}

	httpReq, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	if err != nil {
		return err
	}

	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.APIKey))
	httpReq.Header.Set("Content-Type", "application/json")

	res, err := c.HTTP.Do(httpReq)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(res.Body)
		return fmt.Errorf("anythingLLM error (status %d): %s", res.StatusCode, string(body))
	}

	return nil
}

type QueryResponse struct {
	TextResponse string `json:"textResponse"`
	Sources      []struct {
		Text string `json:"text"`
	} `json:"sources"`
}

func (c *AnythingClient) QueryWorkspace(workspace, message string) (string, error) {
	url := fmt.Sprintf("%s/workspace/%s/chat", c.BaseURL, workspace)
	payload, err := json.Marshal(map[string]interface{}{
		"message": message,
		"mode":    "query",
	})
	if err != nil {
		return "", err
	}

	httpReq, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	if err != nil {
		return "", err
	}

	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.APIKey))
	httpReq.Header.Set("Content-Type", "application/json")

	res, err := c.HTTP.Do(httpReq)
	if err != nil {
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(res.Body)
		return "", fmt.Errorf("anythingLLM query error (status %d): %s", res.StatusCode, string(body))
	}

	var resp QueryResponse
	if err := json.NewDecoder(res.Body).Decode(&resp); err != nil {
		return "", err
	}

	return resp.TextResponse, nil
}
