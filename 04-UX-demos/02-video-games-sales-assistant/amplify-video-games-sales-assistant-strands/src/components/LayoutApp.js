import React from "react";
import { useEffect } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import GlobalStyles from "@mui/material/GlobalStyles";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import SentimentSatisfiedAltIcon from "@mui/icons-material/SentimentSatisfiedAlt";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import Chat from "./Chat";

import { APP_NAME } from "../env";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import CloudOutlinedIcon from "@mui/icons-material/CloudOutlined";

function LayoutApp() {
  const [userName, setUserName] = React.useState("Guest User");
  const [open, setOpen] = React.useState(false);

  const effectRan = React.useRef(false);
  useEffect(() => {
    if (!effectRan.current) {
      console.log("effect applied - only on the FIRST mount");
    }
    return () => (effectRan.current = true);
  }, []);

  const defaultTheme = createTheme({
    palette: {
      primary: {
        main: "#5425AF",
      },
      secondary: {
        main: "#812C90",
      },
    },
  });

  const handleClickOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <ThemeProvider theme={defaultTheme}>
      <GlobalStyles
        styles={{ ul: { margin: 0, padding: 0, listStyle: "none" } }}
      />
      <CssBaseline />
      <AppBar
        position="static"
        color="default"
        elevation={0}
        sx={{
          borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
          background: "#F6F7FD",
        }}
      >
        <Toolbar sx={{ flexWrap: "wrap", p: 1, m: 0 }}>
          <Typography
            variant="h6"
            color="primary"
            noWrap
            sx={{ flexGrow: 1, p: 0, m: 0 }}
          >
            {APP_NAME}
          </Typography>
          <Box sx={{ display: { xs: "none", sm: "inline" } }}>
            <Chip
              sx={{
                border: 0,
                fontSize: "0.95em",
                color: (theme) => theme.palette.primary.dark, // Sets text color to primary dark
                "& .MuiChip-icon": {
                  color: (theme) => theme.palette.primary.dark, // Sets icon color to primary dark
                },
              }}
              label={userName}
              variant="outlined"
              icon={<SentimentSatisfiedAltIcon />}
            />
          </Box>
        </Toolbar>
      </AppBar>
      <Container disableGutters maxWidth="xl" component="main">
        <Chat userName={userName} />
      </Container>
      <Box textAlign={"center"}>
        <Typography
          variant="body2"
          sx={{ pb: 1, pl: 2, pr: 2, fontSize: "0.775rem" }}
        >
          &copy;{new Date().getFullYear()}, Amazon Web Services, Inc. or its
          affiliates. All rights reserved.
        </Typography>
        <img src="/images/Powered-By_logo-horiz_RGB.png" />
      </Box>

      <Box sx={{ position: "fixed", bottom: "8px", right: "12px" }}>
        <IconButton aria-label="" onClick={handleClickOpen}>
          <CloudOutlinedIcon />
        </IconButton>
      </Box>

      <Dialog
        fullWidth={true}
        maxWidth={"xl"}
        open={open}
        onClose={handleClose}
      >
        <DialogTitle>Amazon Bedrock</DialogTitle>
        <DialogContent>
          <img
            src="/images/gen-ai-assistant-diagram.png"
            width={"100%"}
            alt="Powered By AWS"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Close</Button>
        </DialogActions>
      </Dialog>
    </ThemeProvider>
  );
}

export default LayoutApp;
