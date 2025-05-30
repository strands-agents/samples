import React, { useState } from "react";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { styled } from "@mui/material/styles";
import IconButton from "@mui/material/IconButton";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import KeyboardArrowLeftIcon from "@mui/icons-material/KeyboardArrowLeft";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import Tooltip from "@mui/material/Tooltip";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import Pagination from "@mui/material/Pagination";
import Stack from "@mui/material/Stack";

// Create a styled version of TableCell to apply borders and Typography body1 styling
const StyledTableCell = styled(TableCell)(({ theme }) => ({
  border: "1px solid #e0e0e0",
  ...theme.typography.body1,
  padding: theme.spacing(1, 1.5),
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
  maxWidth: "150px", // Limit cell width
}));

// New styled component specifically for header cells with fontWeight 500
const StyledHeaderCell = styled(StyledTableCell)(({ theme }) => ({
  fontWeight: 500,
  backgroundColor: "rgba(245, 247, 250, 0.6)",
}));

// Create a styled version of TableRow to override zebra-striping
const StyledTableRow = styled(TableRow)(({ theme }) => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "transparent",
  },
  "&:nth-of-type(even)": {
    backgroundColor: "rgba(245, 247, 250, 0.6)",
  },
  // Reduce the row height
  "& > .MuiTableCell-root": {
    padding: theme.spacing(0.6, 1.5), // Reduce vertical padding
    height: "auto", // Allow the cell to shrink based on padding
  },
}));

const TableView = ({ query_results }) => {
  const isMobile = useMediaQuery("(max-width:600px)");
  const isSmall = useMediaQuery("(max-width:960px)");

  // Calculate how many columns to show based on screen size
  const columnsToShow = isMobile ? 2 : isSmall ? 5 : 10;

  // Row pagination state
  const ROWS_PER_PAGE = 10;
  const [page, setPage] = useState(1);
  const totalRows = query_results.length;
  const totalPages = Math.ceil(totalRows / ROWS_PER_PAGE);

  // Column navigation state
  const [startColumnIndex, setStartColumnIndex] = useState(0);
  const columnEntries = Object.keys(query_results[0] || {});
  const totalColumns = columnEntries.length;

  const handleColumnNext = () => {
    setStartColumnIndex((prev) =>
      Math.min(prev + 1, totalColumns - columnsToShow)
    );
  };

  const handleColumnPrev = () => {
    setStartColumnIndex((prev) => Math.max(prev - 1, 0));
  };

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  // Calculate visible columns
  const visibleColumnKeys = columnEntries.slice(
    startColumnIndex,
    startColumnIndex + columnsToShow
  );

  // Calculate visible rows for the current page
  const startRowIndex = (page - 1) * ROWS_PER_PAGE;
  const endRowIndex = Math.min(startRowIndex + ROWS_PER_PAGE, totalRows);
  const visibleRows = query_results.slice(startRowIndex, endRowIndex);

  // Format cell values based on their type
  const formatCellValue = (value) => {
    if (value === null || value === undefined) {
      return "-";
    } else if (typeof value === "boolean") {
      return value ? (
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <CheckIcon color="success" fontSize="small" />
        </Box>
      ) : (
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <CloseIcon color="error" fontSize="small" />
        </Box>
      );
    } else {
      return value.toString();
    }
  };

  // Check if tooltip should be shown (only for strings longer than 16 characters)
  const shouldShowTooltip = (value) => {
    return typeof value === "string" && value.length > 16;
  };

  // Get tooltip text for cell values
  const getCellTooltip = (value) => {
    if (shouldShowTooltip(value)) {
      return value;
    }
    return null;
  };

  // Tooltip component wrapper that only renders Tooltip if needed
  const ConditionalTooltip = ({ title, children }) => {
    if (title) {
      return (
        <Tooltip
          title={title}
          arrow
          placement="top"
          componentsProps={{
            tooltip: {
              sx: {
                bgcolor: "white",
                color: "rgba(0, 0, 0, 0.87)",
                boxShadow: "0px 2px 6px rgba(0, 0, 0, 0.15)",
                borderRadius: "4px",
                fontSize: "0.75rem",
                textAlign: "center",
              },
            },
            arrow: {
              sx: {
                color: "white",
              },
            },
          }}
        >
          {children}
        </Tooltip>
      );
    }
    return children;
  };

  return (
    <Box sx={{ width: "100%" }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 1,
        }}
      >
        <Typography variant="caption" color="text.secondary">
          {`Showing columns ${startColumnIndex + 1}-${Math.min(
            startColumnIndex + columnsToShow,
            totalColumns
          )} of ${totalColumns}`}
        </Typography>
        <Box>
          <IconButton
            size="small"
            onClick={handleColumnPrev}
            disabled={startColumnIndex === 0}
          >
            <KeyboardArrowLeftIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            onClick={handleColumnNext}
            disabled={startColumnIndex + columnsToShow >= totalColumns}
          >
            <KeyboardArrowRightIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      <TableContainer
        sx={{
          background: "transparent",
          width: "100%",
          boxShadow: "none",
          overflowX: "auto", // Enable horizontal scrolling if needed
          "&::-webkit-scrollbar": {
            height: "6px",
          },
          "&::-webkit-scrollbar-thumb": {
            backgroundColor: "rgba(0,0,0,0.2)",
            borderRadius: "6px",
          },
        }}
      >
        <Table
          sx={{
            border: "1px solid #e0e0e0",
            width: "100%",
            borderCollapse: "collapse",
            tableLayout: "fixed", // Fixed layout for better performance
            minWidth: isMobile ? "auto" : "250px", // Minimum width to ensure table doesn't get too small
          }}
          size="small"
          aria-label="data table"
        >
          <TableHead>
            <TableRow>
              <StyledHeaderCell sx={{ width: "50px" }}>#</StyledHeaderCell>
              {visibleColumnKeys.map((key, index) => (
                <ConditionalTooltip
                  title={shouldShowTooltip(key) ? key : null}
                  key={`header-${index}`}
                >
                  <StyledHeaderCell
                    sx={{
                      minWidth: isMobile ? "100px" : "120px",
                    }}
                  >
                    {key}
                  </StyledHeaderCell>
                </ConditionalTooltip>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {visibleRows.map((row, rowIndex) => (
              <StyledTableRow key={`row-${rowIndex}`}>
                <StyledTableCell align="right" sx={{ width: "40px" }}>
                  {startRowIndex + rowIndex + 1}
                </StyledTableCell>
                {visibleColumnKeys.map((key, colIndex) => {
                  const value = row[key];
                  const isBoolean = typeof value === "boolean";
                  const isNumber = typeof value === "number";

                  return (
                    <ConditionalTooltip
                      title={getCellTooltip(value)}
                      key={`cell-${rowIndex}-${colIndex}`}
                    >
                      <StyledTableCell
                        align={
                          isBoolean ? "center" : isNumber ? "right" : "left"
                        }
                      >
                        {formatCellValue(value)}
                      </StyledTableCell>
                    </ConditionalTooltip>
                  );
                })}
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Row pagination controls */}
      {totalRows > ROWS_PER_PAGE && (
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            mt: 2,
            alignItems: "center",
          }}
        >
          <Typography variant="caption" color="text.secondary">
            {`Rows ${startRowIndex + 1}-${endRowIndex} of ${totalRows}`}
          </Typography>
          <Stack spacing={2}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={handlePageChange}
              color="primary"
              size={isMobile ? "small" : "medium"}
              showFirstButton={!isMobile}
              showLastButton={!isMobile}
            />
          </Stack>
        </Box>
      )}
    </Box>
  );
};

export default TableView;
