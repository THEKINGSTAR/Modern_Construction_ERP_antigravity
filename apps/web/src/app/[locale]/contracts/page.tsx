import React from 'react';
import { useTranslations } from 'next-intl';

export default function ContractsPage() {
  const t = useTranslations('Contracts');
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">{t('title')}</h1>
      <div className="bg-white p-6 rounded shadow">
        <p className="text-gray-600">{t('coming_soon')}</p>
      </div>
    </div>
  );
}
