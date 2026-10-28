'use client';

import { useEffect, useMemo, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function Home() {
  const [groups, setGroups] = useState([]);
  const [query, setQuery] = useState('');
  const [groupName, setGroupName] = useState('');
  const [subgroup, setSubgroup] = useState('');
  const [calendarUrl, setCalendarUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_URL}/api/groups`)
      .then((response) => {
        if (!response.ok) throw new Error('Не удалось загрузить список групп');
        return response.json();
      })
      .then(setGroups)
      .catch((reason) => setError(reason.message));
  }, []);

  const filteredGroups = useMemo(() => {
    const value = query.trim().toLowerCase();
    return groups
      .filter((group) => group.name.toLowerCase().includes(value))
      .slice(0, 80);
  }, [groups, query]);

  const selectedGroup = groups.find((group) => group.name === groupName);

  function selectGroup(value) {
    setGroupName(value);
    const next = groups.find((group) => group.name === value);
    setSubgroup(next?.subgroups?.[0] || '');
    setCalendarUrl('');
  }

  async function createLink(event) {
    event.preventDefault();
    setError('');
    setCopied(false);
    const fullName = `${groupName} (${subgroup} подгруппа)`;
    try {
      const response = await fetch(`${API_URL}/api/calendar-link?group=${encodeURIComponent(fullName)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Не удалось создать ссылку');
      setCalendarUrl(data.url);
    } catch (reason) {
      setError(reason.message);
    }
  }

  async function copyLink() {
    await navigator.clipboard.writeText(calendarUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <main className="page-shell">
      <nav className="nav"><div className="brand"><span className="brand-mark">S</span> sfu<span>calendar</span></div><div className="nav-caption">Расписание всегда под рукой</div></nav>
      <section className="hero">
        <div className="eyebrow">CALENDAR FOR SFU</div>
        <h1>Твоё расписание.<br /><em>Всегда актуальное.</em></h1>
        <p className="lead">Выбери группу и подпишись на календарь. Новые занятия появятся в телефоне автоматически.</p>
        <form className="card" onSubmit={createLink}>
          <label htmlFor="search">Найди свою группу</label>
          <div className="search-wrap"><span>⌕</span><input id="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Например, КИ26-16/2Б" /></div>
          <select value={groupName} onChange={(event) => selectGroup(event.target.value)} required>
            <option value="">Выбери группу</option>
            {filteredGroups.map((group) => <option value={group.name} key={group.name}>{group.name} · {group.institute}</option>)}
          </select>
          <div className="subgroup-row">
            <div><label htmlFor="subgroup">Подгруппа</label><select id="subgroup" value={subgroup} onChange={(event) => setSubgroup(event.target.value)} disabled={!selectedGroup} required>{selectedGroup?.subgroups.map((item) => <option value={item} key={item}>{item} подгруппа</option>)}</select></div>
            <button type="submit" disabled={!groupName || !subgroup}>Создать календарь <span>→</span></button>
          </div>
        </form>
        {calendarUrl && <div className="result"><div><div className="result-title">Календарь готов</div><div className="result-text">Скопируй ссылку и добавь её как подписной календарь.</div><code>{calendarUrl}</code></div><button className="copy" onClick={copyLink}>{copied ? 'Скопировано ✓' : 'Копировать'}</button></div>}
        {error && <p className="error">{error}</p>}
      </section>
      <footer><span>Apple Calendar</span><span>Google Calendar</span><span>Outlook</span></footer>
    </main>
  );
}
