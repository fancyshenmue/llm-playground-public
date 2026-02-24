package api

import (
	"context"
	"encoding/csv"
	"fmt"
	"os"
	"time"

	"github.com/adshao/go-binance/v2"
)

// BinanceClient wraps the official Binance Go SDK
type BinanceClient struct {
	client *binance.Client
}

// NewBinanceClient creates a new Binance API client (no auth needed for public data)
func NewBinanceClient() *BinanceClient {
	return &BinanceClient{
		client: binance.NewClient("", ""), // Empty API keys for public endpoints
	}
}

// FetchKlines downloads OHLCV candlestick data (max 1000 per call)
func (c *BinanceClient) FetchKlines(symbol, interval string, limit int, startTime int64) ([]*binance.Kline, error) {
	service := c.client.NewKlinesService().
		Symbol(symbol).
		Interval(interval).
		Limit(limit)

	if startTime > 0 {
		service = service.StartTime(startTime)
	}

	klines, err := service.Do(context.Background())

	if err != nil {
		return nil, fmt.Errorf("failed to fetch klines: %w", err)
	}

	return klines, nil
}

// FetchAllKlines downloads all OHLCV data from a start date, bypassing the 1000 limit
func (c *BinanceClient) FetchAllKlines(symbol, interval string, startTime int64) ([]*binance.Kline, error) {
	var allKlines []*binance.Kline
	currentStart := startTime
	batchSize := 1000

	for {
		klines, err := c.FetchKlines(symbol, interval, batchSize, currentStart)
		if err != nil {
			return nil, err
		}

		if len(klines) == 0 {
			break
		}

		allKlines = append(allKlines, klines...)

		// If we got less than batch size, we've reached the end
		if len(klines) < batchSize {
			break
		}

		// Set next start time to the last candle's close time + 1ms
		lastKline := klines[len(klines)-1]
		currentStart = lastKline.CloseTime + 1
	}

	return allKlines, nil
}

// SaveKlinesToCSV converts klines to CSV format compatible with TradingView exports
func SaveKlinesToCSV(klines []*binance.Kline, filepath string) error {
	file, err := os.Create(filepath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Header matching TradingView format
	if err := writer.Write([]string{"time", "open", "high", "low", "close", "volume"}); err != nil {
		return err
	}

	for _, k := range klines {
		// Convert timestamp to readable format
		timestamp := time.Unix(k.OpenTime/1000, 0).Format("2006-01-02 15:04:05")

		row := []string{
			timestamp,
			k.Open,
			k.High,
			k.Low,
			k.Close,
			k.Volume,
		}

		if err := writer.Write(row); err != nil {
			return err
		}
	}

	return nil
}

// TimeframeToInterval converts human-readable timeframes to Binance intervals
func TimeframeToInterval(tf string) string {
	mapping := map[string]string{
		"1m":  "1m",
		"5m":  "5m",
		"15m": "15m",
		"30m": "30m",
		"1h":  "1h",
		"4h":  "4h",
		"1d":  "1d",
		"1w":  "1w",
	}

	if interval, ok := mapping[tf]; ok {
		return interval
	}
	return "1d" // default
}
