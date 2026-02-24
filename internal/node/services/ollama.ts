import { LLMProvider, ChatMessage, LLMConfig } from '../types';
import { ConfigLoader } from './config-loader';

export class OllamaProvider implements LLMProvider {
    async chat(messages: ChatMessage[], config: LLMConfig): Promise<string> {
        let baseUrl = config.baseUrl;
        if (!baseUrl) {
            const appConfig = await ConfigLoader.load();
            baseUrl = appConfig.ollama.api_url || 'http://127.0.0.1:11434';
        }
        const url = `${baseUrl}/api/chat`;
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: config.model,
                    messages: messages,
                    stream: true, // Use streaming to prevent timeout
                    format: config.format,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: response.statusText }));
                throw new Error(`Ollama error [${response.status}]: ${errorData.error || response.statusText}`);
            }

            if (!response.body) {
                throw new Error('No response body received from Ollama');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                const lines = buffer.split('\n');
                // Keep the last partial line in the buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const json = JSON.parse(line);
                        if (json.message && json.message.content) {
                            fullContent += json.message.content;
                        }
                        if (json.done) return fullContent; // Use return instead of break to exit early
                    } catch (e) {
                        console.error('Failed to parse line as JSON:', line);
                    }
                }
            }

            // Process any remaining data in buffer if it exists (though usually done=true means no more data)
            if (buffer.trim()) {
                try {
                    const json = JSON.parse(buffer);
                    if (json.message && json.message.content) {
                        fullContent += json.message.content;
                    }
                } catch (e) {
                    // Ignore, might be truly incomplete
                }
            }

            return fullContent;
        } catch (error: any) {
            console.error('Ollama Chat Fetch Error:', {
                url,
                model: config.model,
                messageCount: messages.length,
                error: error.message,
                cause: error.cause
            });
            throw new Error(`Failed to communicate with Ollama (${config.model} @ ${url}): ${error.message}${error.cause ? ' (Cause: ' + error.cause + ')' : ''}`);
        }
    }

    async listModels(baseUrl?: string): Promise<string[]> {
        let effectiveUrl = baseUrl;
        if (!effectiveUrl) {
            const appConfig = await ConfigLoader.load();
            effectiveUrl = appConfig.ollama.api_url || 'http://127.0.0.1:11434';
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

        try {
            const url = `${effectiveUrl}/api/tags`;
            console.log(`Fetching models from: ${url}`);
            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`Ollama error: ${response.statusText} (${response.status})`);
            }
            const data = await response.json();
            return data.models.map((m: any) => m.name);
        } catch (error: any) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Connection timeout - is Ollama running?');
            }
            throw new Error(`Failed to connect to Ollama: ${error.message}`);
        }
    }
}
