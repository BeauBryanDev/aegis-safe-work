import { Outlet } from "react-router-dom"
import Header from "./Header"
import Footer from "./Footer"
import MobileNavBar from "./MobileNavBar"

const MainLayout = () => {
  return (
    <div className="flex flex-col h-screen">
      <Header />

      <main className="flex-1 overflow-auto p-2">
        <Outlet />
      </main>

      <MobileNavBar />
      <Footer />
    </div>
  )
}

export default MainLayout