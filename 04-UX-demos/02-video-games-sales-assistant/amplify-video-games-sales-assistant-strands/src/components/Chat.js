import React, { useLayoutEffect, useRef, useEffect } from "react";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import SendIcon from "@mui/icons-material/Send";
import Paper from "@mui/material/Paper";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import InputBase from "@mui/material/InputBase";
import Divider from "@mui/material/Divider";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Button from "@mui/material/Button";
import Grow from "@mui/material/Grow";
import Fade from "@mui/material/Fade";
import { v4 as uuidv4 } from "uuid";
import InsightsOutlinedIcon from "@mui/icons-material/InsightsOutlined";
import QuestionAnswerOutlinedIcon from "@mui/icons-material/QuestionAnswerOutlined";
import TableRowsRoundedIcon from "@mui/icons-material/TableRowsRounded";
import { alpha } from "@mui/material/styles";
import {
  WELCOME_MESSAGE,
  MAX_LENGTH_INPUT_SEARCH,
  AGENT_ENDPOINT_URL,
} from "../env";
import MyChart from "./MyChart.js";
import Answering from "./Answering.js";
import QueryResultsDisplay from "./QueryResultsDisplay";
import { getQueryResults, generateChart } from "../utils/AwsCalls";
import MarkdownRenderer from "./MarkdownRenderer.js";

const Chat = ({ userName = "Guest User" }) => {
  const [totalAnswers, setTotalAnswers] = React.useState(0);
  const [enabled, setEnabled] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [controlAnswers, setControlAnswers] = React.useState([]);
  const [answers, setAnswers] = React.useState([]);
  const [query, setQuery] = React.useState("");
  const [sessionId, setSessionId] = React.useState(uuidv4());
  const [errorMessage, setErrorMessage] = React.useState("");
  const [height, setHeight] = React.useState(480);
  const [size, setSize] = React.useState([0, 0]);

  const borderRadius = 8;

  const scrollRef = useRef(null);
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [answers]);

  useLayoutEffect(() => {
    function updateSize() {
      setSize([window.innerWidth, window.innerHeight]);
      const myh = window.innerHeight - 220;
      if (myh < 346) {
        setHeight(346);
      } else {
        setHeight(myh);
      }
    }
    window.addEventListener("resize", updateSize);
    updateSize();
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  const effectRan = React.useRef(false);
  useEffect(() => {
    if (!effectRan.current) {
      console.log("effect applied - only on the FIRST mount");
      const fetchData = async () => {
        console.log("Chat");
      };
      fetchData()
        // catch any error
        .catch(console.error);
    }
    return () => (effectRan.current = true);
  }, []);

  const handleQuery = (event) => {
    if (event.target.value.length > 0 && loading === false && query !== "")
      setEnabled(true);
    else setEnabled(false);
    setQuery(event.target.value.replace(/\n/g, ""));
  };

  const handleKeyPress = (event) => {
    if (event.code === "Enter" && loading === false && query !== "") {
      getAnswer(query);
    }
  };

  const handleClick = async (e) => {
    e.preventDefault();
    if (query !== "") {
      getAnswer(query);
    }
  };

  const getAnswer = async (my_query) => {
    if (!loading && my_query !== "") {
      setControlAnswers((prevState) => [...prevState, {}]);
      setAnswers((prevState) => [...prevState, { query: my_query }]);
      setEnabled(false);
      setLoading(true);
      setErrorMessage("");
      setQuery("");
      try {
        const queryUuid = uuidv4();
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

        let json = {
          text: "",
          queryUuid,
        };

        console.log(queryUuid);

        // Add initial answer object to state
        setControlAnswers((prevState) => [
          ...prevState,
          { current_tab_view: "answer" },
        ]);
        setAnswers((prevState) => [...prevState, json]);

        const params = {
          //bedrock_model_id: "us.anthropic.claude-3-5-haiku-20241022-v1:0", // You can change to the preferred model
          prompt: my_query,
          prompt_uuid: queryUuid,
          user_timezone: timezone,
          session_id: sessionId,
        };
        console.log(params);

        // Initiate streaming response
        const response = await fetch(AGENT_ENDPOINT_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(params),
        });

        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let responseText = "";

        // Read the streaming response
        while (true) {
          const { value, done } = await reader.read();

          if (done) {
            break;
          }

          // Decode the chunk and add it to the response text
          const chunk = decoder.decode(value, { stream: true });
          responseText += chunk;

          // Update the current answer with streaming text
          setAnswers((prev) => {
            const newAnswers = [...prev];
            // Update the last answer (which is the current one)
            const lastIndex = newAnswers.length - 1;
            newAnswers[lastIndex] = {
              ...newAnswers[lastIndex],
              text: responseText,
            };
            return newAnswers;
          });
        }

        console.log("--------- Answer after streaming ------");
        console.log(responseText);

        // After streaming is complete, fetch query results if needed
        const queryResults = await getQueryResults(queryUuid);
        console.log(queryResults);

        setLoading(false);
        setEnabled(false);

        // Update the answer with query results if available
        if (queryResults.length > 0) {
          setAnswers((prev) => {
            const newAnswers = [...prev];
            const lastIndex = newAnswers.length - 1;
            newAnswers[lastIndex] = {
              ...newAnswers[lastIndex],
              chart: "loading",
              queryResults: queryResults,
            };
            return newAnswers;
          });

          // Generate chart if there are query results
          const chart = await generateChart({
            text: responseText,
            queryUuid,
            queryResults,
          });

          // Update the answer with generated chart
          setAnswers((prev) => {
            const newAnswers = [...prev];
            const lastIndex = newAnswers.length - 1;
            newAnswers[lastIndex] = {
              ...newAnswers[lastIndex],
              chart: chart,
            };
            return newAnswers;
          });

          console.log("--------- Answer after chart generation ------");
          console.log({ text: responseText, queryUuid, queryResults, chart });
        } else {
          console.log("------- Answer without chart-------");
          console.log({ text: responseText, queryUuid });
        }

        setTotalAnswers((prevState) => prevState + 1);
      } catch (error) {
        console.log("Call failed: ", error);
        setErrorMessage(error.toString());
        setLoading(false);
        setEnabled(false);
      }
    }
  };

  const handleShowTab = (index, type) => () => {
    const updatedItems = [...controlAnswers];
    updatedItems[index] = { ...updatedItems[index], current_tab_view: type };
    setControlAnswers(updatedItems);
  };

  return (
    <Box sx={{ pl: 2, pr: 2, pt: 0, pb: 0 }}>
      {errorMessage !== "" && (
        <Alert
          severity="error"
          sx={{
            position: "fixed",
            width: "80%",
            top: "65px",
            left: "20%",
            marginLeft: "-10%",
          }}
          onClose={() => {
            setErrorMessage("");
          }}
        >
          {errorMessage}
        </Alert>
      )}

      <Box
        id="chatHelper"
        sx={{
          display: "flex",
          flexDirection: "column",
          height: height,
          overflow: "hidden",
          overflowY: "scroll",
        }}
      >
        {answers.length > 0 ? (
          <ul style={{ paddingBottom: 14, margin: 0, listStyleType: "none" }}>
            {answers.map((answer, index) => (
              <li key={"meg" + index} style={{ marginBottom: 0 }}>
                {answer.hasOwnProperty("text") && answer.text !== "" && (
                  <Box
                    sx={{
                      borderRadius: borderRadius,
                      pl: 1,
                      pr: 1,
                      display: "flex",
                      alignItems: "flex-start",
                      marginBottom: 1,
                    }}
                  >
                    <Box sx={{ pr: 1, pt: 1.5, pl: 0.5 }}>
                      <img
                        src="/images/genai.png"
                        alt="Amazon Bedrock"
                        width={28}
                        height={28}
                      />
                    </Box>
                    <Box sx={{ p: 0, flex: 1 }}>
                      <Box>
                        <Grow
                          in={
                            controlAnswers[index].current_tab_view === "answer"
                          }
                          timeout={{ enter: 600, exit: 0 }}
                          style={{ transformOrigin: "50% 0 0" }}
                          mountOnEnter
                          unmountOnExit
                        >
                          <Box
                            id={"answer" + index}
                            sx={{
                              opacity: 0.8,
                              "&.MuiBox-root": {
                                animation: "fadeIn 0.8s ease-in-out forwards",
                              },
                              mt: 1,
                            }}
                          >
                            <Typography component="div" variant="body1">
                              <MarkdownRenderer content={answer.text} />
                            </Typography>
                          </Box>
                        </Grow>

                        {answer.hasOwnProperty("queryResults") && (
                          <Grow
                            in={
                              controlAnswers[index].current_tab_view ===
                              "records"
                            }
                            timeout={{ enter: 600, exit: 0 }}
                            style={{ transformOrigin: "50% 0 0" }}
                            mountOnEnter
                            unmountOnExit
                          >
                            <Box
                              sx={{
                                opacity: 0.8,
                                "&.MuiBox-root": {
                                  animation: "fadeIn 0.8s ease-in-out forwards",
                                },
                                transform: "translateY(10px)",
                                "&.MuiBox-root-appear": {
                                  transform: "translateY(0)",
                                },
                                mt: 1,
                              }}
                            >
                              <QueryResultsDisplay
                                index={index}
                                answer={answer}
                              />
                            </Box>
                          </Grow>
                        )}

                        {answer.hasOwnProperty("chart") &&
                          answer.chart.hasOwnProperty("chart_type") && (
                            <Grow
                              in={
                                controlAnswers[index].current_tab_view ===
                                "chart"
                              }
                              timeout={{ enter: 600, exit: 0 }}
                              style={{ transformOrigin: "50% 0 0" }}
                              mountOnEnter
                              unmountOnExit
                            >
                              <Box
                                sx={{
                                  opacity: 0.8,
                                  "&.MuiBox-root": {
                                    animation:
                                      "fadeIn 0.9s ease-in-out forwards",
                                  },
                                  transform: "translateY(10px)",
                                  "&.MuiBox-root-appear": {
                                    transform: "translateY(0)",
                                  },
                                  mt: 1,
                                }}
                              >
                                <MyChart
                                  caption={answer.chart.caption}
                                  options={
                                    answer.chart.chart_configuration.options
                                  }
                                  series={
                                    answer.chart.chart_configuration.series
                                  }
                                  type={answer.chart.chart_type}
                                />
                              </Box>
                            </Grow>
                          )}
                      </Box>

                      {answer.hasOwnProperty("queryResults") && (
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "flex-start",
                            gap: 1,
                            py: 1,
                            mt: 1,
                          }}
                        >
                          {answer.queryResults.length > 0 && (
                            <Fade
                              timeout={1000}
                              in={answer.queryResults.length > 0}
                            >
                              <Box
                                sx={{ display: "flex", alignItems: "center" }}
                              >
                                <Button
                                  sx={(theme) => ({
                                    pr: 1,
                                    pl: 1,
                                    "&.Mui-disabled": {
                                      borderBottom: 0.5,
                                      color: theme.palette.primary.main,
                                      borderRadius: 0,
                                    },
                                  })}
                                  data-amplify-analytics-on="click"
                                  data-amplify-analytics-name="click"
                                  data-amplify-analytics-attrs="button:answer-details"
                                  size="small"
                                  color="secondaryText"
                                  disabled={
                                    controlAnswers[index].current_tab_view ===
                                    "answer"
                                  }
                                  onClick={handleShowTab(index, "answer")}
                                  startIcon={<QuestionAnswerOutlinedIcon />}
                                >
                                  Answer
                                </Button>

                                <Button
                                  sx={(theme) => ({
                                    pr: 1,
                                    pl: 1,
                                    "&.Mui-disabled": {
                                      borderBottom: 0.5,
                                      color: theme.palette.primary.main,
                                      borderRadius: 0,
                                    },
                                  })}
                                  data-amplify-analytics-on="click"
                                  data-amplify-analytics-name="click"
                                  data-amplify-analytics-attrs="button:answer-details"
                                  size="small"
                                  color="secondaryText"
                                  disabled={
                                    controlAnswers[index].current_tab_view ===
                                    "records"
                                  }
                                  onClick={handleShowTab(index, "records")}
                                  startIcon={<TableRowsRoundedIcon />}
                                >
                                  Records
                                </Button>

                                {typeof answer.chart === "object" &&
                                  answer.chart.hasOwnProperty("chart_type") && (
                                    <Button
                                      sx={(theme) => ({
                                        pr: 1,
                                        pl: 1,
                                        "&.Mui-disabled": {
                                          borderBottom: 0.5,
                                          color: theme.palette.primary.main,
                                          borderRadius: 0,
                                        },
                                      })}
                                      data-amplify-analytics-on="click"
                                      data-amplify-analytics-name="click"
                                      data-amplify-analytics-attrs="button:answer-details"
                                      size="small"
                                      color="secondaryText"
                                      disabled={
                                        controlAnswers[index]
                                          .current_tab_view === "chart"
                                      }
                                      onClick={handleShowTab(index, "chart")}
                                      startIcon={<InsightsOutlinedIcon />}
                                    >
                                      Chart
                                    </Button>
                                  )}
                              </Box>
                            </Fade>
                          )}

                          {answer.chart === "loading" && (
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                ml: 1,
                              }}
                            >
                              <CircularProgress size={16} color="primary" />
                              <Typography
                                variant="caption"
                                color="secondaryText"
                                sx={{ ml: 1 }}
                              >
                                Generating chart...
                              </Typography>
                            </Box>
                          )}

                          {answer.chart.hasOwnProperty("rationale") && (
                            <Typography variant="caption" color="secondaryText">
                              {answer.chart.rationale}
                            </Typography>
                          )}
                        </Box>
                      )}
                    </Box>
                  </Box>
                )}

                {answer.hasOwnProperty("query") && answer.query !== "" && (
                  <Grid container justifyContent="flex-end">
                    <Box
                      sx={(theme) => ({
                        textAlign: "right",
                        borderRadius: borderRadius,
                        fontWeight: 500,
                        pt: 1,
                        pb: 1,
                        pl: 2,
                        pr: 2,
                        mt: 2,
                        mb: 1.5,
                        mr: 1,
                        boxShadow: "rgba(0, 0, 0, 0.05) 0px 4px 12px",
                        background: `linear-gradient(to right, 
                  ${alpha(theme.palette.primary.light, 0.2)}, 
                  ${alpha(theme.palette.primary.main, 0.2)})`,
                      })}
                    >
                      <Typography color="primary.dark" variant="body1">
                        {answer.query}
                      </Typography>
                    </Box>
                  </Grid>
                )}
              </li>
            ))}

            {loading && (
              <Box sx={{ p: 0, pl: 1, mb: 2, mt: 1 }}>
                <Answering loading={loading} />
              </Box>
            )}

            {/* this is the last item that scrolls into
                    view when the effect is run */}
            <li ref={scrollRef} />
          </ul>
        ) : (
          <Box
            textAlign={"center"}
            sx={{
              pl: 1,
              pt: 1,
              pr: 1,
              pb: 6,
              height: height,
              display: "flex",
              alignItems: "flex-end",
            }}
          >
            <div style={{ width: "100%" }}>
              <img
                src="/images/strands-logo.svg"
                alt="Strands Agents SDK"
                height={128}
              />
              <Typography
                variant="h5"
                sx={(theme) => ({
                  pb: 1,
                  fontWeight: 500,
                  background: `linear-gradient(to right, 
                  ${theme.palette.text.primary}, 
                  ${theme.palette.primary.dark}, 
                  ${theme.palette.text.primary})`,
                  backgroundClip: "text",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  textFillColor: "transparent",
                })}
              >
                Strands Agents SDK
              </Typography>
              <Typography sx={{ pb: 4, fontWeight: 400 }}>
                Open-source framework leveraging modern language models to build powerful AI agents through minimal, model-driven code.
              </Typography>
              <Typography
                color="primary"
                sx={{ fontSize: "1.1rem", pb: 1, fontWeight: 500 }}
              >
                {WELCOME_MESSAGE}
              </Typography>
            </div>
          </Box>
        )}
      </Box>

      <Paper
        component="form"
        sx={(theme) => ({
          zIndex: 0,
          p: 1,
          mb: 2,
          display: "flex",
          alignItems: "center",
          boxShadow:
            "rgba(76, 175, 80, 0.05) 0px 4px 16px, rgba(76, 175, 80, 0.05) 0px 8px 24px, rgba(76, 175, 80, 0.05) 0px 16px 56px",
          borderRadius: 6,
          position: "relative",
          // Remove the default border
          border: "none",
          // Add gradient border using pseudo-element
          "&::before": {
            content: '""',
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            borderRadius: 6,
            padding: "1px", // This creates the border thickness
            background: `linear-gradient(to right, 
                    ${theme.palette.divider}, 
                    ${alpha(theme.palette.primary.main, 0.3)}, 
                    ${theme.palette.divider})`,
            mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
            maskComposite: "xor",
            WebkitMask:
              "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
            WebkitMaskComposite: "xor",
            zIndex: -1,
          },
        })}
      >
        <Box sx={{ pt: 1.5, pl: 0.5 }}>
          <img
            src="/images/AWS_logo_RGB.png"
            alt="Amazon Web Services"
            height={20}
          />
        </Box>
        <InputBase
          required
          id="query"
          name="query"
          placeholder="Type your question..."
          fullWidth
          multiline
          onChange={handleQuery}
          onKeyDown={handleKeyPress}
          value={query}
          variant="outlined"
          inputProps={{ maxLength: MAX_LENGTH_INPUT_SEARCH }}
          sx={{ pl: 1, pr: 2 }}
        />
        <Divider sx={{ height: 32 }} orientation="vertical" />
        <IconButton
          color="primary"
          sx={{ p: 1 }}
          aria-label="directions"
          disabled={!enabled}
          onClick={handleClick}
        >
          <SendIcon />
        </IconButton>
      </Paper>
    </Box>
  );
};

export default Chat;
