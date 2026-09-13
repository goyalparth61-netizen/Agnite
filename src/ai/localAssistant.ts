import type { AnalysisResult, Observation } from './thermalEngine';
import {buildIntelligence} from './intelligence.ts';
import {localAnswer} from './assistantService.ts';

/** Compatibility entry point for the existing local assistant. */
export function answerQuestion(question: string, observations: Observation[], report: AnalysisResult|null, selected?: Observation|null) {
  return localAnswer(question,buildIntelligence(selected === undefined ? observations.reduce<Observation|null>((latest,row)=>!latest||Date.parse(row.observedAt)>Date.parse(latest.observedAt)?row:latest,null) : selected, observations,{landCover:'unknown',industrialDistanceKm:null,windKph:null},report));
}
