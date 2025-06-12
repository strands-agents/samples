import { useState, useEffect } from "react";
import {
  Box,
  Typography,
  IconButton,
  Collapse,
  Tooltip,
  Paper,
  Chip,
} from "@mui/material";
import {
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
} from "@mui/icons-material";
import TableView from "./TableView";

const QueryResultsDisplay = ({ index, answer }) => {
  // State for managing which queries are expanded
  const [expandedQueries, setExpandedQueries] = useState({});
  // State for collapsible paper sections
  const [collapsedPapers, setCollapsedPapers] = useState({});
  // State for copy feedback
  const [copied, setCopied] = useState(false);

  // Initialize state when the component mounts - only the first result will be expanded
  useEffect(() => {
    if (answer?.queryResults?.length > 0) {
      // Initialize with all results collapsed except the first one
      const initialCollapsedState = {};
      answer.queryResults.forEach((_, x) => {
        const resultKey = `table_${index}_${x}`;
        initialCollapsedState[resultKey] = x !== 0; // Only the first result (x === 0) will be expanded
      });
      setCollapsedPapers(initialCollapsedState);
    }
  }, [index, answer]);

  const toggleQueryExpand = (idx) => {
    setExpandedQueries((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const togglePaperCollapse = (idx) => {
    setCollapsedPapers((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const handleCopyQuery = (query) => {
    navigator.clipboard.writeText(query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box>
      {answer.queryResults.map((query_result, x) => {
        const resultKey = `table_${index}_${x}`;
        const hasResults = query_result.query_results.length > 0;
        const isPaperCollapsed = collapsedPapers[resultKey];

        return (
          <Paper
            key={resultKey}
            sx={{
              bgcolor: "rgba(248, 255, 252, 0.05)",
              mb: 2,
              borderRadius: 4,
              overflow: "hidden",
              transition: "all 0.3s ease",
              boxShadow: "rgba(0, 0, 0, 0.05) 0px 4px 12px",
            }}
          >
            {/* Paper Header - Always visible */}
            <Box
              display="flex"
              alignItems="center"
              justifyContent="space-between"
              p={1}
              onClick={() => togglePaperCollapse(resultKey)}
              sx={{
                borderRadius: isPaperCollapsed ? 4 : "4px 4px 0 0",
                cursor: "pointer",
                backgroundColor: isPaperCollapsed
                  ? "rgba(0,0,0,0.03)"
                  : "transparent",
                border: isPaperCollapsed ? "1px solid" : "none",
                borderBottom: !isPaperCollapsed ? "1px solid" : undefined,
                borderColor: "divider",
              }}
            >
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box display="flex" alignItems="center">
                  <Chip
                    label={`Result Set ${x + 1}`}
                    color="primary"
                    size="small"
                    sx={{ mr: 1.5, fontWeight: 500 }}
                  />
                  <Typography variant="body1" sx={{ mr: 2 }}>
                    {query_result.query_description}
                  </Typography>
                </Box>

                <Typography
                  variant="body2"
                  color={hasResults ? "text.primary" : "text.secondary"}
                  fontWeight="medium"
                >
                  {hasResults
                    ? `${query_result.query_results.length} ${
                        query_result.query_results.length === 1
                          ? "record"
                          : "records"
                      }`
                    : "No results"}
                </Typography>
              </Box>

              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  togglePaperCollapse(resultKey);
                }}
              >
                {isPaperCollapsed ? (
                  <KeyboardArrowDownIcon />
                ) : (
                  <KeyboardArrowUpIcon />
                )}
              </IconButton>
            </Box>

            {/* Collapsible Paper Content */}
            <Collapse in={!isPaperCollapsed}>
              <Box p={2}>
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="flex-end"
                  mb={1}
                >
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mr: 1 }}
                  >
                    SQL Query:
                  </Typography>
                  <Tooltip title={copied ? "Copied!" : "Copy query"}>
                    <IconButton
                      size="small"
                      onClick={() => handleCopyQuery(query_result.query)}
                    >
                      <CopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip
                    title={
                      expandedQueries[resultKey] ? "Hide query" : "Show query"
                    }
                  >
                    <IconButton
                      size="small"
                      onClick={() => toggleQueryExpand(resultKey)}
                      sx={{
                        transform: expandedQueries[resultKey]
                          ? "rotate(180deg)"
                          : "rotate(0deg)",
                        transition: "transform 0.3s",
                      }}
                    >
                      <ExpandMoreIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>

                <Collapse in={expandedQueries[resultKey] || false}>
                  <Paper
                    variant="outlined"
                    sx={{
                      mb: 2,
                      p: 1.5,
                      backgroundColor: "rgba(0, 0, 0, 0.02)",
                      borderRadius: 3,
                      fontFamily: "monospace",
                      fontSize: "0.85rem",
                      whiteSpace: "pre-wrap",
                      overflowX: "auto",
                    }}
                  >
                    {query_result.query}
                  </Paper>
                </Collapse>

                {hasResults ? (
                  <TableView query_results={query_result.query_results} />
                ) : (
                  <Typography sx={{ textAlign: "center", py: 2 }}>
                    No Data Records
                  </Typography>
                )}
              </Box>
            </Collapse>
          </Paper>
        );
      })}
    </Box>
  );
};

export default QueryResultsDisplay;
