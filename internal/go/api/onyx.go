package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type OnyxClient struct {
	BaseURL string
	APIKey  string
	HTTP    *http.Client
}

func NewOnyxClient(baseURL, apiKey string) *OnyxClient {
	return &OnyxClient{
		BaseURL: baseURL,
		APIKey:  apiKey,
		HTTP: &http.Client{
			Timeout: 120 * time.Second,
		},
	}
}

type OnyxQueryRequest struct {
	Message       string `json:"message"`
	Stream        bool   `json:"stream"`
	PersonaID     int    `json:"persona_id,omitempty"`
	ChatSessionID string `json:"chat_session_id,omitempty"`
}

type OnyxQueryResponse struct {
	Message string `json:"message"`
}

func (c *OnyxClient) Query(personaID int, projectID int, message string) (string, error) {
	url := fmt.Sprintf("%s/api/chat/send-chat-message", c.BaseURL)

	reqBody := map[string]interface{}{
		"message": message,
		"stream":  false,
	}

	chatSessionInfo := map[string]interface{}{}
	if personaID > 0 {
		chatSessionInfo["persona_id"] = personaID
	}
	if projectID > 0 {
		chatSessionInfo["project_id"] = projectID
	}

	if len(chatSessionInfo) > 0 {
		reqBody["chat_session_info"] = chatSessionInfo
	}

	payload, err := json.Marshal(reqBody)
	if err != nil {
		return "", err
	}

	httpReq, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	if err != nil {
		return "", err
	}

	if c.APIKey != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.APIKey))
	}
	httpReq.Header.Set("Content-Type", "application/json")

	res, err := c.HTTP.Do(httpReq)
	if err != nil {
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(res.Body)
		return "", fmt.Errorf("onyx error (status %d): %s", res.StatusCode, string(body))
	}

	var resp struct {
		Message      string `json:"message"`
		TopDocuments []struct {
			Content string `json:"blurb"`
		} `json:"top_documents"`
	}
	if err := json.NewDecoder(res.Body).Decode(&resp); err != nil {
		return "", err
	}

	result := resp.Message
	if len(resp.TopDocuments) > 0 {
		result += "\n\nSource Documents:\n"
		for _, doc := range resp.TopDocuments {
			if doc.Content != "" {
				result += fmt.Sprintf("---\n%s\n", doc.Content)
			}
		}
	}

	return result, nil
}
