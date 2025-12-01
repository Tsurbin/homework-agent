import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import Chet from './components/Chet'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <Chet />
    </>
  )
}

export default App
