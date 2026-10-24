(function () {
  'use strict';

  var root = document.querySelector('[data-career-review-root]');
  if (!root) return;

  var STORAGE_KEY = 'careerRadar.review.v1';
  var prompts = [
    { key: 'Role', label: '役割', question: 'いまの仕事・役割を、肩書きではなく「何を任されているか」で書いてください。' },
    { key: 'Responsibility', label: '責任', question: '成果責任はどこまでですか。人・予算・顧客・納期など、責任範囲を書いてください。' },
    { key: 'DecisionRights', label: '意思決定', question: '自分で決められることは何ですか。優先順位、予算、採用、仕様、方針などを具体化してください。' },
    { key: 'Achievement', label: '実績', question: '直近で残した成果を一つ。できれば「前→後」の変化で書いてください。' },
    { key: 'Evidence', label: '証拠', question: 'その実績を裏づける数字・成果物・第三者評価・期間・規模はありますか。' },
    { key: 'Risk', label: 'リスク', question: 'いまのキャリアで気になっている弱点や集中リスク、古くなりそうな経験は何ですか。' },
    { key: 'Goal', label: '目標', question: '1〜3年後、どんな役割・働き方・報酬・専門性を選べる状態にしたいですか。' },
    { key: 'Constraint', label: '制約', question: '勤務地、時間、収入下限、家庭、健康、契約など、選択を制限する条件はありますか。' }
  ];

  var memo = root.querySelector('[data-review-memo]');
  var workspace = root.querySelector('[data-review-workspace]');
  var startPanel = root.querySelector('[data-review-start]');
  var result = root.querySelector('[data-review-result]');
  var question = root.querySelector('[data-review-question]');
  var progress = root.querySelector('[data-review-progress]');
  var feedback = root.querySelector('[data-review-feedback]');
  var micButton = root.querySelector('[data-action="mic"]');
  var speakButton = root.querySelector('[data-action="speak"]');
  var recognition = null;
  var micOn = false;
  var speakOn = false;
  var currentIndex = 0;
  var lastVoiceFinal = '';

  function track(name, params) {
    if (typeof window.gtag === 'function') window.gtag('event', name, params || {});
  }

  function safeLoad() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function saveState(reason) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
        memo: memo.value,
        currentIndex: currentIndex,
        updatedAt: new Date().toISOString()
      }));
      track('career_review_save', { reason: reason || 'manual', step: currentIndex + 1 });
      feedback.textContent = 'この端末に保存しました。';
    } catch (e) {
      feedback.textContent = '保存できませんでした。ブラウザの保存設定をご確認ください。';
    }
  }

  function lineValue(label) {
    var escaped = label.replace(/[.*+?^$()|[\]\\]/g, '\\$&');
    var re = new RegExp('(?:^|\\n)' + escaped + '：\\s*([^\\n]*)', 'm');
    var match = memo.value.match(re);
    return match ? match[1].trim() : '';
  }

  function ensureLabel(index) {
    var label = prompts[index].label + '：';
    var re = new RegExp('(?:^|\\n)' + prompts[index].label + '：', 'm');
    if (!re.test(memo.value)) {
      memo.value = memo.value.replace(/\s+$/, '');
      memo.value += (memo.value ? '\n\n' : '') + label + ' ';
      memo.focus();
      memo.setSelectionRange(memo.value.length, memo.value.length);
    }
  }

  function completedCount() {
    return prompts.filter(function (p) { return lineValue(p.label).length >= 2; }).length;
  }

  function firstMissingIndex() {
    for (var i = 0; i < prompts.length; i += 1) {
      if (lineValue(prompts[i].label).length < 2) return i;
    }
    return prompts.length;
  }

  function renderStep() {
    currentIndex = firstMissingIndex();
    progress.textContent = completedCount() + ' / ' + prompts.length;
    if (currentIndex >= prompts.length) {
      completeReview();
      return;
    }
    question.textContent = prompts[currentIndex].question;
    ensureLabel(currentIndex);
    track('career_review_step', { step: currentIndex + 1, slot: prompts[currentIndex].key });
    if (speakOn) speak(question.textContent);
  }

  function startReview() {
    startPanel.hidden = true;
    result.hidden = true;
    workspace.hidden = false;
    var saved = safeLoad();
    if (saved && typeof saved.memo === 'string' && saved.memo.trim()) {
      memo.value = saved.memo;
      feedback.textContent = '前回のCareer Memoを復元しました。';
    }
    track('career_review_start', { resumed: !!(saved && saved.memo) });
    renderStep();
  }

  function nextStep() {
    var value = lineValue(prompts[currentIndex].label);
    if (value.length < 2) {
      feedback.textContent = '現在の問いについて、Career Memoに一言以上書いてください。';
      memo.focus();
      return;
    }
    feedback.textContent = '';
    saveState('step');
    renderStep();
  }

  function list(items) {
    return '<ul>' + items.map(function (x) { return '<li>' + escapeHtml(x) + '</li>'; }).join('') + '</ul>';
  }

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>"']/g, function (ch) {
      return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch];
    });
  }

  function axis(name, state, note) {
    return '<article class="review-axis"><div class="review-axis-head"><h3>' + escapeHtml(name) + '</h3><span>' + escapeHtml(state) + '</span></div><p>' + escapeHtml(note) + '</p></article>';
  }

  function completeReview() {
    saveState('complete');
    workspace.hidden = true;
    result.hidden = false;

    var role = lineValue('役割');
    var responsibility = lineValue('責任');
    var decision = lineValue('意思決定');
    var achievement = lineValue('実績');
    var evidence = lineValue('証拠');
    var risk = lineValue('リスク');
    var goal = lineValue('目標');
    var constraint = lineValue('制約');

    root.querySelector('[data-result-position]').innerHTML = list([
      role || '役割の記述を追加してください。',
      responsibility ? '責任範囲: ' + responsibility : '責任範囲をもう少し具体化できます。',
      decision ? '意思決定: ' + decision : '意思決定権の所在がまだ曖昧です。'
    ]);

    root.querySelector('[data-result-capital]').innerHTML = list([
      achievement ? '実績: ' + achievement : '持ち運べる実績を一つ作る余地があります。',
      evidence ? '証拠: ' + evidence : '成果を裏づける数字・成果物・第三者評価を増やす余地があります。',
      decision ? '判断経験は、役割名より強いキャリア資本になり得ます。' : '判断経験を言語化すると市場で伝わりやすくなります。'
    ]);

    var risks = [];
    if (risk) risks.push(risk);
    if (!evidence) risks.push('成果の証拠が弱いと、経験の再現性が外部に伝わりにくくなります。');
    if (!decision) risks.push('意思決定範囲が不明確だと、上位役割への移行材料が弱くなります。');
    if (constraint) risks.push('制約条件: ' + constraint);
    root.querySelector('[data-result-risk]').innerHTML = list(risks.length ? risks : ['大きなギャップは未特定です。市場テストで外部評価を確認してください。']);

    root.querySelector('[data-result-options]').innerHTML = list([
      goal ? '目標に近い役割へ直接応募し、市場反応を測る。' : 'まず1〜3年後の到達状態を明確にする。',
      evidence ? '現在の実績をCase Card化し、別企業・別案件でも通用するか試す。' : '数字・成果物・第三者評価のどれか一つを追加する。',
      risk ? '最大のリスクを減らす小さな副業・学習・案件テストを置く。' : '一つの会社・職種だけに依存しない選択肢を1本増やす。'
    ]);

    root.querySelector('[data-result-actions]').innerHTML = list([
      'Career Memoから最も説明しやすい実績を1件選び、「課題 / 自分の判断 / 結果 / 証拠」の4行にする。',
      '今週中に1つの市場テストを行い、応募・スカウト・知人・案件相談の反応を記録する。',
      '反応が弱かった場合は自己否定ではなく、役割・証拠・対象市場のどこがずれたかを見直す。'
    ]);

    var evidenceStrong = evidence.length >= 8;
    var decisionStrong = decision.length >= 8;
    var portabilityStrong = achievement.length >= 8 && evidenceStrong;
    var scarcityStrong = /専門|希少|業界|技術|資格|経営|AI|データ|営業|医療|金融|法務|PM|PMO/i.test(memo.value);
    var optionalityStrong = /副業|業務委託|転職|独立|複数|案件|スカウト|紹介/i.test(memo.value);
    var concentrationRisk = /一社|1社|一人|一人だけ|単一|依存|顧客集中|業界だけ|社内だけ/i.test(memo.value) || risk.length >= 8;

    root.querySelector('[data-axis-grid]').innerHTML = [
      axis('Evidence', evidenceStrong ? '根拠あり' : '補強余地', evidenceStrong ? '数字・成果物・第三者評価など、外部に説明できる材料があります。' : '成果を示す証拠を一つ追加すると市場テストの精度が上がります。'),
      axis('Decision Rights', decisionStrong ? '明確' : '要整理', decisionStrong ? '自分が引き受けた判断を説明できます。' : '「参加した」ではなく「自分が決めたこと」を切り分けてください。'),
      axis('Portability', portabilityStrong ? '持ち運びやすい' : '検証余地', portabilityStrong ? '成果と証拠がセットなので、別環境でも説明しやすい状態です。' : 'その成果が別会社でも再現できる条件を整理してください。'),
      axis('Scarcity', scarcityStrong ? '仮説あり' : '未確認', scarcityStrong ? '専門性・業界性・判断経験に希少性の仮説があります。市場反応で確認してください。' : '「誰でもできる作業」と「経験者ほど差が出る判断」を分けてみてください。'),
      axis('Optionality', optionalityStrong ? '複線あり' : '増やせる', optionalityStrong ? '複数の働き方・市場接点につながる材料があります。' : '転職だけでなく、副業・業務委託・社内異動などの小さな選択肢を増やせます。'),
      axis('Concentration Risk', concentrationRisk ? '要確認' : '大きな兆候なし', concentrationRisk ? '一社・一顧客・一業界・一つのスキルへの依存度を確認してください。' : '入力内容から強い集中リスクは見えていませんが、定期的な再確認が必要です。')
    ].join('');

    track('career_review_complete', { completed_slots: completedCount() });
    track('career_review_result_view', { completed_slots: completedCount() });
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function speak(text) {
    if (!('speechSynthesis' in window) || !text) return;
    window.speechSynthesis.cancel();
    var utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'ja-JP';
    window.speechSynthesis.speak(utter);
  }

  function setupRecognition() {
    var Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      micButton.disabled = true;
      micButton.textContent = '音声入力 非対応';
      return;
    }
    recognition = new Recognition();
    recognition.lang = 'ja-JP';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = function (event) {
      var finalText = '';
      for (var i = event.resultIndex; i < event.results.length; i += 1) {
        if (event.results[i].isFinal) finalText += event.results[i][0].transcript;
      }
      finalText = finalText.trim();
      if (!finalText || finalText === lastVoiceFinal) return;
      lastVoiceFinal = finalText;
      memo.value = memo.value.replace(/\s+$/, '') + (memo.value ? ' ' : '') + finalText;
      memo.dispatchEvent(new Event('input', { bubbles: true }));
    };
    recognition.onerror = function () {
      feedback.textContent = '音声入力を続けられませんでした。テキスト入力はそのまま使えます。';
      micOn = false;
      micButton.setAttribute('aria-pressed', 'false');
      micButton.textContent = '音声入力 OFF';
    };
    recognition.onend = function () {
      if (micOn) {
        try { recognition.start(); } catch (e) {}
      }
    };
  }

  root.addEventListener('click', function (event) {
    var target = event.target.closest('[data-action]');
    if (!target) return;
    var action = target.getAttribute('data-action');
    if (action === 'start') startReview();
    if (action === 'next') nextStep();
    if (action === 'save') saveState('manual');
    if (action === 'restart') {
      result.hidden = true;
      workspace.hidden = false;
      renderStep();
    }
    if (action === 'mic' && recognition) {
      micOn = !micOn;
      target.setAttribute('aria-pressed', micOn ? 'true' : 'false');
      target.textContent = micOn ? '音声入力 ON' : '音声入力 OFF';
      if (micOn) {
        try { recognition.start(); } catch (e) {}
      } else {
        try { recognition.stop(); } catch (e) {}
      }
    }
    if (action === 'speak') {
      speakOn = !speakOn;
      target.setAttribute('aria-pressed', speakOn ? 'true' : 'false');
      target.textContent = speakOn ? '読み上げ ON' : '読み上げ OFF';
      if (speakOn) speak(question.textContent);
      else if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    }
  });

  memo.addEventListener('input', function () {
    feedback.textContent = '';
  });

  var articleLink = root.querySelector('[data-review-article-link]');
  if (articleLink) articleLink.addEventListener('click', function () {
    track('career_review_article_click', { source_path: window.location.pathname, target_path: articleLink.getAttribute('href') });
  });

  var marketLink = root.querySelector('[data-review-market-test]');
  if (marketLink) marketLink.addEventListener('click', function () {
    track('career_review_market_test_click', { provider: 'assign', placement: 'career_review_market_test' });
  });

  setupRecognition();
  track('career_review_view', { page_path: window.location.pathname });

  var saved = safeLoad();
  if (saved && saved.memo) {
    startPanel.querySelector('.small').textContent = '前回のCareer Memoがあります。「始める」で続きから再開できます。入力内容はこの端末だけに保存されています。';
  }
})();