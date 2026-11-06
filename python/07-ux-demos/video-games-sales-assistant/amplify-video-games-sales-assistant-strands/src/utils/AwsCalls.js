import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";
import { fetchAuthSession } from "aws-amplify/auth";
import { createAwsClient } from "./AwsAuth";
import { extractBetweenTags, removeCharFromStartAndEnd, handleFormatter } from "./Utils.js";
import {
  AGENT_ENDPOINT_URL,
  MODEL_ID_FOR_CHART,
  CHART_PROMPT
} from "../env.js";

/**
 * Get the SQL queries and results the agent ran for a prompt.
 * The agent only returns results for prompts sent by the signed-in user.
 *
 * @param {string} queryUuid - The prompt_uuid sent to the agent
 * @returns {Promise<Array>} - Objects with query, query_results, and query_description
 */
export const getQueryResults = async (queryUuid = "") => {
  try {
    const headers = {};
    try {
      const session = await fetchAuthSession();
      const authToken = session.tokens?.idToken?.toString();
      if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      }
    } catch (authError) {
      console.warn("Could not get auth token:", authError);
    }

    const url = new URL(
      `/query-results/${encodeURIComponent(queryUuid)}`,
      AGENT_ENDPOINT_URL
    );

    console.log("------- Get Query Results -------");
    console.log(url.toString());

    const response = await fetch(url, { headers });
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error getting query results:", error);
    throw error;
  }
};

/**
 * Generates a chart based on answer and data
 * @param {Object} answer - Answer object containing text
 * @returns {Object} Chart configuration or rationale for no chart
 */
export const generateChart = async (
  answer
) => {
  const bedrock = await createAwsClient(BedrockRuntimeClient);
  let query_results = "";
  for (let i = 0; i < answer.queryResults.length; i++) {
    query_results += JSON.stringify(answer.queryResults[i].query_results) + "\n";
  }

  // Prepare the prompt
  let new_chart_prompt = CHART_PROMPT.replace(
    /<<answer>>/i,
    answer.text
  ).replace(/<<data_sources>>/i, query_results);

  const payload = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 2000,
    temperature: 1,
    messages: [
      {
        role: "user",
        content: [{ type: "text", text: new_chart_prompt }],
      },
    ],
  };

  try {
    // Send the request to Bedrock
    console.log("------- Request chart -------");
    console.log(payload);

    const command = new InvokeModelCommand({
      contentType: "application/json",
      body: JSON.stringify(payload),
      modelId: MODEL_ID_FOR_CHART,
    });

    const apiResponse = await bedrock.send(command);
    const decodedResponseBody = new TextDecoder().decode(apiResponse.body);
    const responseBody = JSON.parse(decodedResponseBody).content[0].text;

    console.log("------- Response chart generation -------");
    console.log(responseBody);

    // Process the response
    const has_chart = parseInt(extractBetweenTags(responseBody, "has_chart"));

    if (has_chart) {
      const chartConfig = JSON.parse(
        extractBetweenTags(responseBody, "chart_configuration")
      );
      const chart = {
        chart_type: removeCharFromStartAndEnd(
          extractBetweenTags(responseBody, "chart_type"),
          "\n"
        ),
        chart_configuration: handleFormatter(chartConfig),
        caption: removeCharFromStartAndEnd(
          extractBetweenTags(responseBody, "caption"),
          "\n"
        ),
      };

      console.log("------- Final chart generation -------");
      console.log(chart);

      return chart;
    } else {
      return {
        rationale: removeCharFromStartAndEnd(
          extractBetweenTags(responseBody, "rationale"),
          "\n"
        ),
      };
    }
  } catch (error) {
    console.error("Chart generation failed:", error);
    return {
      rationale: "Error generating or parsing chart data.",
    };
  }
};


