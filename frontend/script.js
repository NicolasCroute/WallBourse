const API_URL = 
  window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://wallbourse-backend.onrender.com"

// I.
// -----------------------------
// ----------- LOGIN -----------
// -----------------------------
window.onload = () => {
  const isLogged = localStorage.getItem("userId");
  if(isLogged){
    document.getElementById("loginSection").style.display = "none";
    document.getElementById("mainSection").style.display = "block";
    afficherPortefeuilles()
    afficherUtilisateur()
  }
};


document.getElementById("loginForm").onsubmit = async (e) => {
  e.preventDefault();
  const nom = e.target.nom.value;
  const prenom = e.target.prenom.value;

  // mettre les donné entré en JSON
  const res = await fetch(`${API_URL}/login`,{
    method:"POST",
    headers: { "Content-Type":"application/json"},
    body: JSON.stringify({ nomutilisateur: nom, prenomutilisateur: prenom })
  });

  // Verif si serveur a envoyé du code
  if(res.ok){
    // recupère le user
    const user = await res.json();
    //stock dans le navigateur :
    localStorage.setItem("userId", user.idUtilisateur)

    document.getElementById("loginSection").style.display = "none";
    document.getElementById("mainSection").style.display = "block";

    afficherUtilisateur()
    afficherPortefeuilles()
  }
  else{
    alert("Utilisateur non trouvé !")
  }
}

// II.
let deuxiemeSection = document.getElementById("idDeuxiemeSection");
let vosActions = document.getElementById("vosActions");
vosActions.addEventListener('click', () =>{
  deuxiemeSection.scrollIntoView({behavior: 'smooth'});
})

// --------------------------
// --- UTILISATEUR PRECIS ---
// --------------------------
async function afficherUtilisateur() {
  const userid = localStorage.getItem("userId");
  if(!userid) return;

  const res = await fetch(`${API_URL}/utilisateur/${userid}`);
  const data = await res.json();

  console.log(data)

  let nomPrenomUser = document.getElementById("nomPrenomUser");
  let prenomUser = data.prenomutilisateur
  let prenomUserFomat = prenomUser.charAt(0).toUpperCase() + prenomUser.slice(1).toLowerCase() 
  nomPrenomUser.innerHTML= data.nomutilisateur.toUpperCase() + " " + prenomUserFomat;
}


// -------------------------------------
// --- PORTEFEUILLES PAR UTILISATEUR ---
// -------------------------------------
const suppressionPortefeuille = document.getElementById("suppressionPortefeuille");
const select = document.getElementById("listePortefeuilles");

async function afficherPortefeuilles() {
  const userid = localStorage.getItem("userId");
  if(!userid) return;

  const res = await fetch(`${API_URL}/utilisateur/${userid}/portefeuilles`);
  const data = await res.json() 

  //---Liste déroulante---
  select.innerHTML = "";

  const defaultOption = document.createElement("option");
  defaultOption.textContent = "Total";
  defaultOption.value = "";
  defaultOption.selected = true; 
  select.appendChild(defaultOption)

  data.forEach(p => {
    const option = document.createElement("option");
    option.textContent = p.nomportefeuille;
    option.value = p.idportefeuille;
    select.appendChild(option);
  });


  suppressionPortefeuille.style.display = "none";
  afficherToutesLesActions(userid)

  select.onchange = () =>{
    const idPortefeuilleActif = select.value
    localStorage.setItem("portefeuilleActifID", idPortefeuilleActif)

    if(idPortefeuilleActif)
    {
      suppressionPortefeuille.style.display = "block";
      afficherActions(idPortefeuilleActif)
    }
    else
    {
      suppressionPortefeuille.style.display = "none";
      afficherToutesLesActions(userid)
    }
  }
}



// -------------------------------
// --- Action par portefeuille ---
// -------------------------------
const tbody = document.querySelector(".tableAction tbody")

async function afficherActions(idportefeuille){
  const res = await fetch(`${API_URL}/portefeuille/${idportefeuille}/actions`);
  const data = await res.json()

  //---Prix total---
  const prixTotal = document.getElementById("prixTotal");
  prixTotal.innerHTML = parseFloat(data.totalportefeuille).toFixed(2) + " €"

  //---Tableau---
  tbody.innerHTML = "";

  data.actions.forEach(a => {
    const tr = document.createElement("tr");

    const tdNomAction = document.createElement("td");
    tdNomAction.textContent = a.nomaction;

    const tdQuantite = document.createElement("td");
    tdQuantite.textContent = a.quantiteaction;

    const tdGainJourEuro = document.createElement("td");
    tdGainJourEuro.textContent = "0 €";

    const tdGainJourPourcent = document.createElement("td");
    tdGainJourPourcent.textContent = "0 %";

    const tdGainTotalEuro = document.createElement("td");
    tdGainTotalEuro.textContent = "0 €";

    const tdGainTotalPourcent = document.createElement("td");
    tdGainTotalPourcent.textContent = "0 %";

    tr.appendChild(tdNomAction);
    tr.appendChild(tdQuantite);
    tr.appendChild(tdGainJourEuro);
    tr.appendChild(tdGainJourPourcent);
    tr.appendChild(tdGainTotalEuro);
    tr.appendChild(tdGainTotalPourcent);

    tbody.appendChild(tr);
  });
}


async function afficherToutesLesActions(iduser){
  const res = await fetch(`${API_URL}/utilisateur/${iduser}/actions`);
  const data = await res.json()

  //---Prix total---
  const prixTotal = document.getElementById("prixTotal");
  prixTotal.innerHTML = parseFloat(data.totalportefeuille).toFixed(2) + " €"

  //---Tableau---
  tbody.innerHTML = "";
  
  data.actions.forEach(a => {
    const tr = document.createElement("tr");

    const tdNomAction = document.createElement("td");
    tdNomAction.textContent = a.nomaction;

    const tdQuantite = document.createElement("td");
    tdQuantite.textContent = a.quantiteaction;

    const tdGainJourEuro = document.createElement("td");
    tdGainJourEuro.textContent = "0 €";

    const tdGainJourPourcent = document.createElement("td");
    tdGainJourPourcent.textContent = "0 %";

    const tdGainTotalEuro = document.createElement("td");
    tdGainTotalEuro.textContent = "0 €";

    const tdGainTotalPourcent = document.createElement("td");
    tdGainTotalPourcent.textContent = "0 %";

    tr.appendChild(tdNomAction);
    tr.appendChild(tdQuantite);
    tr.appendChild(tdGainJourEuro);
    tr.appendChild(tdGainJourPourcent);
    tr.appendChild(tdGainTotalEuro);
    tr.appendChild(tdGainTotalPourcent);

    tbody.appendChild(tr);
  });
}

// -----------------------------------
// --- Ajout Portefeuille (Modale) ---
// -----------------------------------

const btnAjoutPortefeuille = document.getElementById("ajoutPortefeuille");
const modal = document.getElementById("modalAjout");
const fermerAjout = document.getElementById("fermerModalAjoutPortefeuille");
const formAjoutPortefeuille = document.getElementById("formAjoutPortefeuille");

btnAjoutPortefeuille.addEventListener("click", function (e) {
  chargerOption();
  modal.style.display = "block";
});

fermerAjout.addEventListener("click", function (e) {
  modal.style.display = "none";
});

window.addEventListener("click", function (e) {
  if (e.target === modal) {
    modal.style.display = "none";
  }
});

formAjoutPortefeuille.addEventListener("submit", async function (e) {
  e.preventDefault()
  
  const idTypePortefeuille = parseInt(e.target.nomTypePortefeuille.value);
  const idPlateforme = parseInt(e.target.nomPlateforme.value);
  const nom = e.target.nom.value;
  const montant = parseFloat(e.target.montant.value) || 0;
  const datePremierVersement = e.target.datePremierVersement.value;

  const iduser = localStorage.getItem("userId");
  
  const res = await fetch(`${API_URL}/portefeuille`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      idutilisateur: parseInt(iduser),
      nomportefeuille: nom,
      totalportefeuille: montant,
      dateouverture: datePremierVersement,
      idtypeportefeuille: idTypePortefeuille,
      idplateforme: idPlateforme
    })
  });

  if (res.ok){
    alert("Portefeuille ajouté ! ");
    document.getElementById("modalAjout").style.display = "none";
    afficherPortefeuilles();
  }
  else{
    alert("Erreur lors de l'ajout")
  }
})

// ---- Recuperation type & plateforme ----
async function chargerOption() {
  // Type portefeuille
  const resType = await fetch(`${API_URL}/type-portefeuille`);
  const dataType = await resType.json() 

  let selectTypePortefeuille = document.getElementById("selectTypePortefeuille");
  selectTypePortefeuille.innerHTML = "";

  dataType.forEach(t => {
    const optionType = document.createElement("option");
    optionType.textContent = t.nomtypeportefeuille;
    optionType.value = t.idtypeportefeuille;
    selectTypePortefeuille.appendChild(optionType);
  });

  // Plateforme
  const resPlateforme = await fetch(`${API_URL}/plateforme`);
  const dataPlateforme = await resPlateforme.json() 

  let selectPlateforme = document.getElementById("selectPlateforme");
  selectPlateforme.innerHTML = "";

  dataPlateforme.forEach(p => {
    const optionPlateforme = document.createElement("option");
    optionPlateforme.textContent = p.nomplateforme;
    optionPlateforme.value = p.idplateforme;
    selectPlateforme.appendChild(optionPlateforme);
  });


}




// --------------------------------
// --- Suppression Portefeuille ---
// --------------------------------
suppressionPortefeuille.addEventListener("click", async () => {
  const id = select.value;

  if(!id) return;

  const confirmation = confirm("Voulez-vous vraiment supprimer ce portefeuille ?")
  if(!confirmation) return;

  const res = await fetch(`${API_URL}/portefeuille/${id}`, {
    method: "DELETE"
  });

  if(res.ok){
    alert("Portefeuille supprimé !")
    afficherPortefeuilles();
  }
  else{
    alert("Erreur lors de la suppression")
  }
})



// --------------------
// --- Ajout Action ---
// --------------------
async function chargerListePortefeuille(nomIdSelectPortefeuille) {
  let iduser = localStorage.getItem("userId");

  const res = await fetch(`${API_URL}/utilisateur/${iduser}/portefeuilles`);
  const data = await res.json() 

  let selectPortefeuilleAction = document.getElementById(nomIdSelectPortefeuille);
  selectPortefeuilleAction.innerHTML = "";

  let portefeuilleActifID = localStorage.getItem("portefeuilleActifID")

  data.forEach(p => {
    const option = document.createElement("option");
    option.textContent = p.nomportefeuille;
    option.value = p.idportefeuille;
    if(p.idportefeuille == parseInt(portefeuilleActifID)){
      option.selected = true;
    }
    selectPortefeuilleAction.appendChild(option);
  });
}

//----MODALE-----
const btnAchatAction = document.getElementById("achatAction");
const modalAchat = document.getElementById("modalAchatAction");
const fermerModalAchat = document.getElementById("fermerModalAchat");
const formAchatAction = document.getElementById("formAchatAction");

btnAchatAction.addEventListener("click", function (e) {
  chargerListePortefeuille("selectPortefeuilleActionAchat");
  modalAchat.style.display = "block";
});

fermerModalAchat.addEventListener("click", function (e) {
  modalAchat.style.display = "none";
});

window.addEventListener("click", function (e) {
  if (e.target === modalAchat) {
    modalAchat.style.display = "none";
  }
});


formAchatAction.addEventListener("submit", async function (e) {
  e.preventDefault();

  let nomActionValue = e.target.nomAction.value;
  let symbolActionVAlue = e.target.symbolAction.value;
  let quantiteActionValue = Math.floor(e.target.quantiteAction.value);
  let dateAchatActionValue = e.target.dateAchatAction.value;
  let montantInitActionValue = e.target.montantInitAction.value;
  let idportefeuilleValue = parseInt(document.getElementById("selectPortefeuilleActionAchat").value)
  let portefeuilleActifID = localStorage.getItem("portefeuilleActifID")

  const res = await fetch(`${API_URL}/action`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      nomaction: nomActionValue,
      symbol: symbolActionVAlue,
      quantiteaction: quantiteActionValue,
      dateachataction: dateAchatActionValue,
      prixachataction: montantInitActionValue,
      idportefeuille: idportefeuilleValue
    })
  });

  if (res.ok){
    alert("Action ajouté ! ");
    modalAchat.style.display = "none";
    
    if(portefeuilleActifID)
    {
      suppressionPortefeuille.style.display = "block";
      afficherActions(parseInt(portefeuilleActifID));
    }
    else
    {
      suppressionPortefeuille.style.display = "none";
      const userId = localStorage.getItem("userId");
      afficherToutesLesActions(userId);
    }
  }
  else{
    alert("Erreur lors de l'ajout")
  }
})

// --------------------
// --- Vente Action ---
// --------------------

async function chargerActionLierPortefeuille() {
  let choixPortefeuille = document.getElementById("selectPortefeuilleActionVente").value;
  console.log("choixPortefeuille : " + choixPortefeuille)

  const res = await fetch(`${API_URL}/portefeuille/${choixPortefeuille}/actions`);

  if(!res.ok){
    alert("Créer d'abord un portefeuille")
    return;
  }
    
  const data = await res.json()

  let selectActionVendre = document.getElementById("selectActionVendre");
  selectActionVendre.innerHTML = "";

  data.actions.forEach(a => {
    let optionVente = document.createElement("option");
    optionVente.textContent = a.nomaction;
    optionVente.value = a.idaction;
    selectActionVendre.appendChild(optionVente);
  });
}


//----MODALE-----
const btnVenteAction = document.getElementById("venteAction");
const modalVente = document.getElementById("modalVenteAction");
const fermerModalVente = document.getElementById("fermerModalVente");
const formVenteAction = document.getElementById("formVenteAction");

btnVenteAction.addEventListener("click", async function (e) {
  await chargerListePortefeuille("selectPortefeuilleActionVente");
  chargerActionLierPortefeuille();
  modalVente.style.display = "block";
});

document.getElementById("selectPortefeuilleActionVente").addEventListener("change", () =>{
  chargerActionLierPortefeuille();
})

fermerModalVente.addEventListener("click", function (e) {
  modalVente.style.display = "none";
});

window.addEventListener("click", function (e) {
  if (e.target === modalVente) {
    modalVente.style.display = "none";
  }
});

formVenteAction.addEventListener("submit", async function (e) {
  e.preventDefault();

  let portefeuilleActifID = localStorage.getItem("portefeuilleActifID")
  let idaction = parseInt(document.getElementById("selectActionVendre").value);
  const quantite = parseInt(e.target.quantiteActionVente.value)

  if(!idaction || !quantite || quantite <= 0){
    alert("Selectioner une action et une quantité valide")
    return;
  } 

  const confirmation = confirm("Voulez-vous vraiment vendre cette action ?")
  if(!confirmation) return;

  const res = await fetch(`${API_URL}/action/${idaction}?quantite=${quantite}`, {
    method: "DELETE",
  });

  if(res.ok){
    alert("Action vendu !")
    modalVente.style.display = "none";
    
    if(portefeuilleActifID)
    {
      afficherActions(parseInt(portefeuilleActifID));
    }
    else
    {
      const userId = localStorage.getItem("userId");
      afficherToutesLesActions(userId);
    }
  }
  else{
    alert("Erreur lors de la vente")
  }
})


