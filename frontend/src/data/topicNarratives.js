/** 各讲本地叙事：优先于（或兜底）后端步骤卡，便于标注教案/PPT 位置 */

import { overviewIntroStory, overviewStepDetails } from "./overviewContent.js";
import { narrativesCh456 } from "./topicNarratives_ch456.js";
import { narrativesCh781011 } from "./topicNarratives_ch781011.js";

export const topicNarratives = {
  decision_overview: {
    intro_story: overviewIntroStory,
    step_details: overviewStepDetails,
  },
  ...narrativesCh456,
  ...narrativesCh781011,
};

export function narrativeFor(methodId) {
  return topicNarratives[methodId] || null;
}
