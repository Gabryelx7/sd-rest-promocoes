import React, { useState, useEffect } from 'react';

const API_BASE = "http://127.0.0.1:5000";

function App() {
  const [promotions, setPromotions] = useState([]);
  const [interests, setInterests] = useState([]);
  const [newInterest, setNewInterest] = useState("");
  const [notifications, setNotifications] = useState([]);
  const [clientId, setClientId] = useState(() => {
  const savedId = localStorage.getItem("app_client_id");
    return savedId || "CLIENTE_TESTE_1";
  });
  
  useEffect(() => {
    if (clientId) {
      localStorage.setItem("app_client_id", clientId);
    }
  }, [clientId]);

  // REST API: Fetch Promotions
  const fetchPromotions = async () => {
    if (!clientId) return;
    
    try {
      const response = await fetch(`${API_BASE}/promotions`, {
        headers: { 'X-Client-Id': clientId }
      });
      const data = await response.json();
      
      setPromotions(Object.values(data));
    } catch (error) {
      console.error("Erro ao buscar promoções:", error);
    }
  };

  // REST API: Fetch Interests
  const fetchInterests = async () => {
    if (!clientId) return;

    try {
      const response = await fetch(`${API_BASE}/interests`, {
        headers: { 'X-Client-Id': clientId }
      });

      if (!response.ok) {
        console.error("Erro ao buscar interesses:", response.statusText);
        return;
      }

      const data = await response.json();
      setInterests(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Erro ao buscar interesses:", error);
    }
  };

  // Fetch promotions on initial load
  useEffect(() => {
    fetchPromotions();
  }, []);

  useEffect(() => {
    if (!clientId) return;
    fetchInterests();
  }, [clientId]);

  // SSE: Real-Time Notifications ---
  useEffect(() => {
    if (!clientId) return;

    // Open connections
    const globalSse = new EventSource(`${API_BASE}/stream`);
    const privateSse = new EventSource(`${API_BASE}/stream?channel=${clientId}`);

    const handleNotification = (event, type) => {
      const data = JSON.parse(event.data);
      const newNotification = {
        id: Date.now(),
        type: type,
        message: type === 'hotdeal' 
          ? `🔥 HOT DEAL: ${data.Mensagem}` 
          : `🛒 NOVA PROMOÇÃO: ${data.Produto} por R$${data.Preço} (${data.Título})`
      };

      setNotifications((prev) => [newNotification, ...prev]);

      // Automatically remove notification after 8 seconds
      setTimeout(() => {
        setNotifications((prev) => prev.filter(n => n.id !== newNotification.id));
      }, 8000);

      // Refresh the promotions list so the user sees the new data automatically
      fetchPromotions();
    };

    globalSse.addEventListener('hotdeal', (e) => handleNotification(e, 'hotdeal'));
    privateSse.addEventListener('category', (e) => handleNotification(e, 'category'));

    // Cleanup listeners on component unmount to prevent memory leaks
    return () => {
      globalSse.close();
      privateSse.close();
    };
  }, [clientId]);

  // --- REST API: Voting ---
  const handleVote = async (promoId, voteValue) => {
    try {
      await fetch(`${API_BASE}/promotions/${promoId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voto: voteValue })
      });
      // Re-fetch to update the score on the screen
      fetchPromotions();
    } catch (error) {
      console.error("Erro ao registrar voto:", error);
    }
  };

  // --- REST API: Manage Interests ---
  const handleAddInterest = async (e) => {
    e.preventDefault();
    if (!newInterest) return;

    try {
      await fetch(`${API_BASE}/interests`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Client-Id': clientId 
        },
        body: JSON.stringify({ interesse: newInterest.toLowerCase() })
      });
      
      if (!interests.includes(newInterest.toLowerCase())) {
        setInterests([...interests, newInterest.toLowerCase()]);
      }
      setNewInterest("");

      fetchInterests();
    } catch (error) {
      console.error("Erro ao adicionar interesse:", error);
    }
  };

  const handleRemoveInterest = async (category) => {
    try {
      await fetch(`${API_BASE}/interests`, {
        method: 'DELETE',
        headers: { 
          'Content-Type': 'application/json',
          'X-Client-Id': clientId 
        },
        body: JSON.stringify({ interesse: category })
      });
      setInterests(interests.filter(i => i !== category));
      fetchInterests();
    } catch (error) {
      console.error("Erro ao remover interesse:", error);
    }
  };

  // --- UI Render ---
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '1000px', margin: '0 auto' }}>
      <h1>Painel do Consumidor</h1>
      
      {/* Client ID Configuration */}
      <div style={styles.section}>
        <label><b>ID do Cliente: </b></label>
        <input 
          value={clientId} 
          onChange={(e) => setClientId(e.target.value)}
          style={{ padding: '5px', marginLeft: '10px' }}
        />
      </div>

      {/* Floating Notifications Area */}
      <div style={styles.notificationContainer}>
        {notifications.map(notif => (
          <div key={notif.id} style={{
            ...styles.notification,
            backgroundColor: notif.type === 'hotdeal' ? '#ffebee' : '#e3f2fd',
            borderColor: notif.type === 'hotdeal' ? '#ef5350' : '#42a5f5'
          }}>
            {notif.message}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '20px' }}>
        {/* Left Column: Interests */}
        <div style={{ flex: 1 }}>
          <div style={styles.section}>
            <h3>Meus Interesses</h3>
            <form onSubmit={handleAddInterest} style={{ marginBottom: '15px' }}>
              <input 
                placeholder="Ex: jogo, livro..." 
                value={newInterest} 
                onChange={(e) => setNewInterest(e.target.value)}
                style={{ padding: '8px', width: '60%' }}
              />
              <button type="submit" style={{ padding: '8px 15px', marginLeft: '5px', cursor: 'pointer' }}>
                Seguir
              </button>
            </form>
            
            <ul style={{ paddingLeft: '20px' }}>
              {interests.length === 0 ? <p>Nenhum interesse cadastrado.</p> : null}
              {interests.map(interesse => (
                <li key={interesse} style={{ marginBottom: '10px' }}>
                  <b>{interesse}</b>
                  <button 
                    onClick={() => handleRemoveInterest(interesse)}
                    style={{ marginLeft: '10px', color: 'red', cursor: 'pointer' }}
                  >
                    Remover
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right Column: Promotions List */}
        <div style={{ flex: 2 }}>
          <div style={styles.section}>
            <h3>Promoções Publicadas</h3>
            {promotions.length === 0 ? <p>Nenhuma promoção disponível no momento.</p> : null}
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {promotions.map(promo => (
                <div key={promo.id} style={styles.card}>
                  <div>
                    <h4 style={{ margin: '0 0 5px 0' }}>{promo.produto}</h4>
                    <p style={{ margin: 0, color: '#666' }}>Categoria: {promo.categoria}</p>
                    <h3 style={{ margin: '10px 0', color: '#2e7d32' }}>R$ {promo.preco.toFixed(2)}</h3>
                  </div>
                  
                  <div style={{ textAlign: 'center', backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '5px' }}>
                    <p style={{ margin: '0 0 10px 0' }}>Votos: <b>{promo.votos}</b></p>
                    <button onClick={() => handleVote(promo.id, 1)} style={styles.upvote}>+1</button>
                    <button onClick={() => handleVote(promo.id, -1)} style={styles.downvote}>-1</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Basic styling objects
const styles = {
  section: {
    border: '1px solid #ddd',
    padding: '20px',
    borderRadius: '8px',
    backgroundColor: '#fff',
    marginBottom: '20px'
  },
  card: {
    border: '1px solid #ccc',
    padding: '15px',
    borderRadius: '8px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fafafa'
  },
  upvote: {
    padding: '5px 15px', backgroundColor: '#4caf50', color: 'white', border: 'none', borderRadius: '3px', marginRight: '5px', cursor: 'pointer'
  },
  downvote: {
    padding: '5px 15px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer'
  },
  notificationContainer: {
    position: 'fixed', top: '20px', right: '20px', zIndex: 1000, width: '300px'
  },
  notification: {
    padding: '15px', marginBottom: '10px', borderRadius: '5px', borderLeft: '5px solid', boxShadow: '0 2px 5px rgba(0,0,0,0.2)', animation: 'fadeIn 0.3s ease-in-out'
  }
};

export default App;