import { Outlet } from "react-router-dom"
import Header from "./Header"
import Footer from "./Footer"
import MobileNavBar from "./MobileNavBar"
import DesktopSideBar from "./DesktopSideBar"
import { useTelemetry } from "../hooks/useTelemetry"

const MainLayout = () => {
  // Mock telemetry driver — mounted ONCE here to bring all stores alive.
  useTelemetry()

  return (
    <div className="flex h-screen flex-col">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <DesktopSideBar />
        <main className="flex-1 overflow-y-auto p-3 pb-20 md:pb-3">
          <Outlet />
        </main>
      </div>

      <MobileNavBar />
      <Footer />
    </div>
  )
}

export default MainLayout
