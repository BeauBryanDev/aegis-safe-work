import { Navigate } from "react-router-dom"

/** Home redirects to the dashboard (the "/" route renders Dashboard directly). */
const Home = () => <Navigate to="/" replace />

export default Home
