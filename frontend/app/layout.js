import './globals.css';

export const metadata = {
  title: 'Расписание СФУ',
  description: 'Подписка на расписание СФУ',
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
