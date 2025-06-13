// 주차 계산 유틸리티 (프론트엔드용)
export function getWeeksOfMonth(year, month) {
  // month: 1~12
  // "해당 주의 토요일이 속한 달"이 기준 달이면 포함
  const weeks = [];
  // 기준 달의 첫째날~마지막날
  const firstDayOfMonth = new Date(year, month - 1, 1);
  const lastDayOfMonth = new Date(year, month, 0);
  // 기준 달의 첫 주 일요일 찾기 (이전달 포함)
  let start = new Date(firstDayOfMonth);
  start.setDate(start.getDate() - start.getDay()); // 그 주의 일요일로 이동
  let week = 1;
  while (true) {
    const end = new Date(start);
    end.setDate(end.getDate() + 6); // 토요일
    // 토요일이 기준 달에 속하면 포함
    if ((end.getMonth() + 1) === month) {
      weeks.push({
        week,
        start: new Date(start),
        end: new Date(end)
      });
      week++;
    }
    // 기준 달의 마지막날이 토요일이거나, 토요일이 이미 기준 달을 넘으면 종료
    if (end >= lastDayOfMonth) break;
    start.setDate(start.getDate() + 7);
  }
  return weeks;
}
