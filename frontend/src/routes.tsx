import { Routes, Route } from "react-router-dom"
import Dashboard from "../pages/Dashboard"
import Metrics from "../pages/Metrics"
import Alerts from "../pages/Alerts"
import Logs from "../pages/Logs"
import Settings from "../pages/Settings"
import MainLayout from "../layouts/MainLayout"
import Home from "../pages/Home"
import { useState } from "react"

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}