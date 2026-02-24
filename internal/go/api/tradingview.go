package api

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
)

// Candle represents a single OHLC candle from TradingView
type Candle struct {
	Time   string
	Open   float64
	High   float64
	Low    float64
	Close  float64
	Volume float64
}

// Trade represents a single trade from the TradingView Strategy Tester Trade List
type Trade struct {
	TradeNum    int
	Type        string
	DateTime    string
	Signal      string
	Price       float64
	SizeQty     float64
	SizeValue   float64
	NetPnL      float64
	NetPnLPerc  float64
	MaxRunUp    float64
	MaxDrawdown float64
}

// ParseTradingViewCSV parses a CSV file exported from TradingView (ISO Time format)
func ParseTradingViewCSV(filePath string, limit int) ([]Candle, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	// TradingView CSVs often have headers: time, open, high, low, close, volume
	records, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}

	if len(records) < 2 {
		return nil, fmt.Errorf("csv file is empty or missing headers")
	}

	var candles []Candle
	start := 1 // Skip header
	if limit > 0 && len(records)-1 > limit {
		start = len(records) - limit
	}

	for i := start; i < len(records); i++ {
		record := records[i]
		if len(record) < 5 {
			continue
		}

		c := Candle{
			Time: record[0],
		}

		c.Open, _ = strconv.ParseFloat(record[1], 64)
		c.High, _ = strconv.ParseFloat(record[2], 64)
		c.Low, _ = strconv.ParseFloat(record[3], 64)
		c.Close, _ = strconv.ParseFloat(record[4], 64)
		if len(record) > 5 {
			c.Volume, _ = strconv.ParseFloat(record[5], 64)
		}

		candles = append(candles, c)
	}

	return candles, nil
}

// FormatCandlesForLLM converts candles to a concise text description for LLM context
func FormatCandlesForLLM(candles []Candle) string {
	res := "Market Data (Last Candles):\n"
	for _, c := range candles {
		res += fmt.Sprintf("Time: %s, O: %.2f, H: %.2f, L: %.2f, C: %.2f\n",
			c.Time, c.Open, c.High, c.Low, c.Close)
	}
	return res
}

// ParseTradeListCSV parses the Trade List export from TradingView Strategy Tester
func ParseTradeListCSV(filePath string) ([]Trade, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}

	if len(records) < 2 {
		return nil, fmt.Errorf("trade list csv is empty or missing headers")
	}

	var trades []Trade
	// Header: Trade #, Type, Date and time, Signal, Price, Position size (qty), Position size (value), Net P&L, Net P&L %, Favorable excursion, Adverse excursion, Cumulative P&L, Cumulative P&L %
	for i := 1; i < len(records); i++ {
		record := records[i]
		if len(record) < 13 {
			continue
		}

		t := Trade{
			Type:     record[1],
			DateTime: record[2],
			Signal:   record[3],
		}

		t.TradeNum, _ = strconv.Atoi(record[0])
		t.Price, _ = strconv.ParseFloat(record[4], 64)
		t.SizeQty, _ = strconv.ParseFloat(record[5], 64)
		t.SizeValue, _ = strconv.ParseFloat(record[6], 64)
		t.NetPnL, _ = strconv.ParseFloat(record[7], 64)
		t.NetPnLPerc, _ = strconv.ParseFloat(record[8], 64)
		t.MaxRunUp, _ = strconv.ParseFloat(record[10], 64)    // Favorable excursion %
		t.MaxDrawdown, _ = strconv.ParseFloat(record[12], 64) // Adverse excursion %

		trades = append(trades, t)
	}

	return trades, nil
}

// FormatTradesForLLM converts trades to a performance summary for the Analyst
func FormatTradesForLLM(trades []Trade) string {
	if len(trades) == 0 {
		return "No trade history available.\n"
	}

	res := "Strategy Performance (Trade List):\n"
	winCount := 0
	totalPnL := 0.0
	for _, t := range trades {
		// Only look at "Exit" trades for PnL summary
		if t.Type == "Exit long" || t.Type == "Exit short" {
			res += fmt.Sprintf("Trade #%d (%s): PnL: %.2f (%.2f%%), MaxRunUp: %.2f%%, MaxDD: %.2f%%\n",
				t.TradeNum, t.Signal, t.NetPnL, t.NetPnLPerc, t.MaxRunUp, t.MaxDrawdown)
			if t.NetPnL > 0 {
				winCount++
			}
			totalPnL += t.NetPnL
		}
	}

	exitCount := 0
	for _, t := range trades {
		if t.Type == "Exit long" || t.Type == "Exit short" {
			exitCount++
		}
	}

	if exitCount > 0 {
		res += fmt.Sprintf("\nSummary: Total Trades: %d, Win Rate: %.2f%%, Total PnL: %.2f\n",
			exitCount, float64(winCount)/float64(exitCount)*100, totalPnL)
	}
	return res
}
