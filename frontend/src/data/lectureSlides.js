/**
 * 每讲「课件讲解」：课堂真实 PPT 导出的图片页。
 * 图片在 frontend/public/lectures/{ch}/slide-XX.jpg
 * 重建：python scripts/build_lecture_decks.py
 * 口播：knowledge/narration/chN.md → 每页 narration
 * 源文件：资源/_解压_教学PPT/教学PPT/*.pptx（第九讲对应 11 多属性决策）
 */
import generated from "./lectureDecks.generated.json";

/** @type {Record<string, {chapterId:string,title:string,chapterTitle:string,methodId:string,topicId:string,sourceFile?:string,slides:Array}>} */
export const lectureDecks = generated;

export function deckForChapter(chapterId) {
  return lectureDecks[chapterId] || null;
}

export function hasLectureDeck(chapterId) {
  return !!lectureDecks[chapterId]?.slides?.length;
}
