import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import ScraperControl from './pages/ScraperControl';
import Companies from './pages/Companies';
import SalaryIntelligence from './pages/SalaryIntelligence';
import Analytics from './pages/Analytics';
import ExportCenter from './pages/ExportCenter';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="scraper" element={<ScraperControl />} />
          <Route path="companies" element={<Companies />} />
          <Route path="salary" element={<SalaryIntelligence />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="export" element={<ExportCenter />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

