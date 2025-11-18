// chart-pie-demo.js (Chart.js v4, 방탄 버전)
(function () {
  // 0) Chart.js 로딩 확인
  if (typeof Chart === 'undefined') {
    console.warn('[Pie] Chart.js not loaded yet.');
    return;
  }

  const el = document.getElementById('myPieChart');
  if (!el) {
    console.warn('[Pie] #myPieChart not found.');
    return;
  }

  // 1) Jinja -> JS 변환: 문자열로 들어온 경우도 안전하게 처리
  const toArray = (x) => {
    if (Array.isArray(x)) return x;
    if (typeof x === 'string') {
      try { return JSON.parse(x); } catch { return []; }
    }
    return x == null ? [] : [x];
  };

  const labels = toArray(window.PjinjaLabels);
  const values = toArray(window.PjinjaValues).map(v => Number(v));

  // 2) 데이터 검증
  if (!labels.length || !values.length) {
    console.warn('[Pie] Empty labels/values', { labels, values });
  }

  // 3) Chart.js v4 글로벌 폰트
  Chart.defaults.font.family =
    '-apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
  Chart.defaults.color = '#292b2c';

  // 4) 팔레트 길이 < 데이터 길이 대비
  const palette = [
    '#36A2EB', '#FF6384', '#4BC0C0', '#AE85FF',
    '#FF9F40', '#FFCD56', '#C9CBCF', '#B3E5D1',
    '#B2C7E6', '#F5CFE7', '#D3D0F4', '#F3E5D1',
    '#EFD5D5', '#DCDCDC'
  ];
  const colors = Array.from({ length: values.length }, (_, i) => palette[i % palette.length]);

  // 5) 차트 생성 (v4)
  new Chart(el, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors, borderWidth: 1 }]
    },
    options: {
      responsive: true,
      cutout: '60%',
      plugins: {
        legend: { position: 'left' },
        title: { display: false }
      }
    }
  });
})();
