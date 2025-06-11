// 주차 계산 유틸리티 (프론트엔드용)
export function getWeeksOfMonth(year, month) {
  // month: 1~12
  const weeks = [];
  const firstDay = new Date(year, month - 1, 1);
  let start = new Date(firstDay);
  let week = 1;
  while (start.getMonth() === firstDay.getMonth()) {
    const end = new Date(start);
    end.setDate(start.getDate() + 6 - start.getDay()); // 토요일까지
    if (end.getMonth() !== firstDay.getMonth()) {
      end.setDate(new Date(year, month, 0).getDate()); // 그 달의 마지막 날
    }
    weeks.push({
      week,
      start: new Date(start),
      end: new Date(end),
    });
    week++;
    start = new Date(end);
    start.setDate(start.getDate() + 1);
  }
  return weeks;
}
