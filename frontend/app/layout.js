import './globals.css';

export const metadata = {
  title: 'SFU Calendar',
  description: 'Подписка на расписание СФУ',
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
