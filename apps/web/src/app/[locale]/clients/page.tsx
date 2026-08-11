import { useTranslations } from 'next-intl';

export default function ClientsPage() {
  const t = useTranslations('Clients');
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">{t('title')}</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500">{t('description')}</p>
        <div className="mt-4">
          <p>Clients dashboard shell loaded.</p>
        </div>
      </div>
    </div>
  );
}
