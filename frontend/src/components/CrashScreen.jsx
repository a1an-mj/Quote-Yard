import { Component } from 'react'

// If a page breaks, show a way out instead of a blank screen.
export default class CrashScreen extends Component {
  state = { broken: false }

  static getDerivedStateFromError() {
    return { broken: true }
  }

  componentDidCatch(error) {
    console.error(error)
  }

  componentDidUpdate(previous) {
    // Moving to another page tries again.
    if (this.state.broken && previous.page !== this.props.page) this.setState({ broken: false })
  }

  render() {
    if (!this.state.broken) return this.props.children
    return (
      <main className="qy-wrap" style={{ paddingBlock: '64px' }}>
        <div className="qy-empty" role="alert">
          <h1 className="qy-h2">Something went wrong on this page</h1>
          <p className="qy-small">Your saved items and alerts are safe. Reload the page or go back home.</p>
          <div className="qy-row" style={{ flexWrap: 'wrap', justifyContent: 'center' }}>
            <button className="qy-btn qy-btn--primary" type="button" onClick={() => window.location.reload()}>Reload</button>
            <a className="qy-btn" href="/home">Home</a>
          </div>
        </div>
      </main>
    )
  }
}
