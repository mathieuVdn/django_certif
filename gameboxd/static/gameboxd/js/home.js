document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("game-search");
    const resultsBox = document.getElementById("autocomplete-results");
  
    input.addEventListener("input", async () => {
      const query = input.value.trim();
      if (query.length < 2) {
        resultsBox.innerHTML = "";
        resultsBox.style.display = "none";
        return;
      }
  
      try {
        const res = await fetch(`/search-games/?q=${encodeURIComponent(query)}`);
        const games = await res.json();
  
        resultsBox.innerHTML = "";
        games.forEach(game => {
          const item = document.createElement("div");
          item.classList.add("autocomplete-item");
          item.textContent = game.title;
          item.onclick = () => {
            input.value = game.title;
            resultsBox.innerHTML = "";
            resultsBox.style.display = "none";
            window.location.href = `/games/${game.id}`;
          };
          resultsBox.appendChild(item);
        });
  
        resultsBox.style.display = "block";
  
      } catch (err) {
        console.error("Erreur recherche :", err);
      }
    });
  });
  