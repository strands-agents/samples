import React, { useState, useEffect } from "react";
import Chart from "react-apexcharts";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import { useTheme } from "@mui/material/styles";
import Divider from "@mui/material/Divider";
import MarkdownRenderer from "./MarkdownRenderer.js";

const MyChart = ({ caption, options, series, type }) => {
  const theme = useTheme();
  const [isVisible, setIsVisible] = useState(false);
  const [chartSeries, setChartSeries] = useState([]);
  const [chartOptions, setChartOptions] = useState({});

  useEffect(() => {
    // Start visibility transition for fade-in effect
    const visibilityTimer = setTimeout(() => {
      setIsVisible(true);
    }, 100);

    // Start series data animation by setting the actual data with a delay
    const seriesTimer = setTimeout(() => {
      setChartSeries(series);
    }, 300);

    return () => {
      clearTimeout(visibilityTimer);
      clearTimeout(seriesTimer);
    };
  }, [series]);

  useEffect(() => {
    // Apply additional chart configurations
    const enhancedOptions = { ...options };
    if (!enhancedOptions.chart) {
      enhancedOptions.chart = {};
    }
    enhancedOptions.chart.zoom = { enabled: false };
    enhancedOptions.chart.animations = { enabled: true };
    if (
      enhancedOptions.chart.type === "bar" &&
      (!enhancedOptions.chart.stacked ||
        enhancedOptions.chart.stacked === false)
    ) {
      enhancedOptions.dataLabels = {
        enabled: false,
      };
    }
    if (enhancedOptions.title) {
      enhancedOptions.title.align = "center";
    }
    if (enhancedOptions.subtitle) {
      enhancedOptions.subtitle.align = "center";
    }
    setChartOptions(enhancedOptions);
  }, [options]);

  return (
    <Box>
      <Box
        sx={{
          bgcolor: "rgba(248, 255, 252, 0.2)",
          p: 2,
          pb: 0,
          m: 0,
          mb: 0,
          borderRadius: 4,
          overflow: "hidden",
          transition: "opacity 0.8s ease-in, transform 0.8s ease-out",
          boxShadow: "rgba(0, 0, 0, 0.05) 0px 4px 12px",
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? "translateY(0)" : "translateY(20px)",
        }}
      >
        <ErrorBoundary
          fallback={
            <Alert severity="error">
              Failed to render chart. Please check your chart configuration.
            </Alert>
          }
        >
          <Chart
            options={chartOptions}
            series={chartSeries}
            type={type}
            height="420px"
            width="100%"
          />
        </ErrorBoundary>
        <Divider sx={{ mt: 2, mb: 2, opacity: 0.5 }} />
        <Typography component="div" variant="body1">
          <MarkdownRenderer content={caption} />
        </Typography>
      </Box>
    </Box>
  );
};

// Error Boundary component to catch render errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Chart error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

export default MyChart;
