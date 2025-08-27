const API_URL = 
  window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://wallbourse-backend.onrender.com"


async function getUtilisateurActuel() {
  const token = localStorage.getItem("token")
  const res = await fetch(`${API_URL}/utilisateur/mes-donnees`,{
    headers:{
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    }
  });

  if (!res.ok) throw new Error("Non authentifié")
  return await res.json();
}

function getToken() {
  return localStorage.getItem("token");
}



// I.
// -----------------------------
// ----------- LOGIN -----------
// -----------------------------
window.onload = () => {
  const token = localStorage.getItem("token");
  if(!token) return;

  try {
    document.getElementById("loginSection").style.display = "none";
    document.getElementById("mainSection").style.display = "block";
    afficherPortefeuilles()
    afficherUtilisateur()
  }
  catch{
    console.warn("Utilisateur non connecté");
  }
};

document.getElementById("formConnexion").onsubmit = async (e) => {
  e.preventDefault();

  // mettre les donné entré en JSON
  const res = await fetch(`${API_URL}/login`,{
    headers: {
      "Content-Type": "application/json",
    },
    method:"POST",
    body: JSON.stringify(
      { 
        emailutilisateur: e.target.emailutilisateur.value, 
        motsdepasseutilisateur: e.target.motsdepasseutilisateur.value 
      })
  });

  // Verif si serveur a envoyé du code
  if(res.ok){
    // recupère le user
    const data = await res.json();
    //stock dans le navigateur :
    localStorage.setItem("token", data.access_token);
    console.log("Token stocké :", data.access_token);

    document.getElementById("loginSection").style.display = "none";
    document.getElementById("mainSection").style.display = "block";

    afficherUtilisateur()
    afficherPortefeuilles()
  }
  else{
    alert("Utilisateur non trouvé !")
  }
}

// -----------------------------------
// ----------- INSCRIPTION -----------
// -----------------------------------

const partieConnexion = document.getElementById("partieConnexion");
const partieInscription = document.getElementById("partieInscription");
const lienPageInscription = document.getElementById("lienInscription");
const lienPageConnexion = document.getElementById("lienConnexion");
const formInscription = document.getElementById("formInscription");

lienPageInscription.addEventListener('click', () =>{
  partieConnexion.style.display = "none";
  partieInscription.style.display = "block";
})

lienPageConnexion.addEventListener('click', () =>{
  partieInscription.style.display = "none";
  partieConnexion.style.display = "block";
})


formInscription.addEventListener('submit', async (e) =>{
  e.preventDefault()
  
  const nom = e.target.nomutilisateur.value;
  const prenom = e.target.prenomutilisateur.value;
  const email = e.target.emailutilisateur.value;
  const motsdepasse = e.target.motsdepasseutilisateur.value;
  
  const res = await fetch(`${API_URL}/inscription`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      nomutilisateur: nom,
      prenomutilisateur: prenom,
      emailutilisateur: email,
      motsdepasseutilisateur: motsdepasse
    })
  });

  if (res.ok){
    document.getElementById("loginSection").style.display = "none";
    document.getElementById("mainSection").style.display = "block";

    afficherPortefeuilles()
    afficherUtilisateur()
  }
  else{
    const err = await res.json();
    alert("Erreur : " + err.detail)
  }
  

})

// II.
// --------------------------------------
// ----------- MENU DEROULANT -----------
// --------------------------------------

let accederMenu = document.getElementById("accederMenuId");
let menuDeroulantId = document.getElementById("menuDeroulantId");
let sectionMenuDeroulant = document.getElementById("sectionMenuDeroulantId");
let choixMenu = document.querySelectorAll(".choixMenu p");


accederMenu.addEventListener("click", (e) =>{
  e.stopPropagation()
  accederMenu.classList.add("hidden");
  menuDeroulantId.style.display = "block";
})

document.addEventListener("click", (e) => {
  if (!sectionMenuDeroulant.contains(e.target)){
    accederMenu.classList.remove("hidden");
    menuDeroulantId.style.display = "none";
  }
})

choixMenu.forEach(element => {
    element.addEventListener("mouseenter", () =>{
        element.classList.add("styleChoixMenu");
    })

    element.addEventListener("mouseleave", () =>{
        element.classList.remove("styleChoixMenu");
    })
});

let btnDeconnexion = document.getElementById("btnDeconnexion");
let btnDashBoard = document.getElementById("btnDashBoard");

btnDeconnexion.addEventListener("click", () =>{
  localStorage.removeItem("portefeuilleActifID");
  localStorage.removeItem("token");
  window.location.replace("index.html")
})

btnDashBoard.addEventListener("click", () =>{
    accederMenu.classList.remove("hidden");
    menuDeroulantId.style.display = "none";
})




// III.
let deuxiemeSection = document.getElementById("idDeuxiemeSection");
let vosActions = document.getElementById("vosActions");
vosActions.addEventListener('click', () =>{
  deuxiemeSection.scrollIntoView({behavior: 'smooth'});
})

// --------------------------
// --- UTILISATEUR PRECIS ---
// --------------------------
async function afficherUtilisateur() {
  const utilisateur = await getUtilisateurActuel();

  let nomPrenomUser = document.getElementById("nomPrenomUser");
  let prenomUser = utilisateur.prenomutilisateur
  let prenomUserFomat = prenomUser.charAt(0).toUpperCase() + prenomUser.slice(1).toLowerCase() 
  nomPrenomUser.innerHTML = utilisateur.nomutilisateur.toUpperCase() + " " + prenomUserFomat;
}


// -------------------------------------
// --- PORTEFEUILLES PAR UTILISATEUR ---
// -------------------------------------
const suppressionPortefeuille = document.getElementById("suppressionPortefeuille");
const select = document.getElementById("listePortefeuilles");

async function afficherPortefeuilles() {
  const utilisateur = await getUtilisateurActuel();

  const res = await fetch(`${API_URL}/utilisateur/${utilisateur.idutilisateur}/portefeuilles`,{
    headers: {
      "Authorization": `Bearer ${getToken()}`
    }
  });
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
  afficherToutesLesActions(utilisateur.idutilisateur)
  
  const interval = localStorage.getItem("interval");
  afficherGraphiqueEvolutionGenerique(`${API_URL}/utilisateur/${utilisateur.idutilisateur}/evolution?interval=${interval}`)

  select.onchange = () =>{
    const idPortefeuilleActif = select.value
    localStorage.setItem("portefeuilleActifID", idPortefeuilleActif)

    if(idPortefeuilleActif)
    {
      suppressionPortefeuille.style.display = "block";
      afficherActions(idPortefeuilleActif)

      const interval = localStorage.getItem("interval");
      afficherGraphiqueEvolutionGenerique(`${API_URL}/portefeuille/${idPortefeuilleActif}/evolution?interval=${interval}`)
    }
    else
    {
      suppressionPortefeuille.style.display = "none";
      afficherToutesLesActions(utilisateur.idutilisateur)

      const interval = localStorage.getItem("interval");
      afficherGraphiqueEvolutionGenerique(`${API_URL}/utilisateur/${utilisateur.idutilisateur}/evolution?interval=${interval}`)
    }
  }
}



// -------------------------------
// --- Action par portefeuille ---
// -------------------------------
const tbody = document.querySelector(".tableAction tbody")

async function afficherActions(idportefeuille){
  const res = await fetch(`${API_URL}/portefeuille/${idportefeuille}/actions`,{
    headers: {
      "Authorization": `Bearer ${getToken()}`
    }
  });
  const data = await res.json();
  afficherListeActions(data);

  const resEtat = await fetch(`${API_URL}/portefeuille/${idportefeuille}/etat`, {
    headers: { "Authorization": `Bearer ${getToken()}` }
  });
  if(resEtat.ok){
    const etat = await resEtat.json();
    document.getElementById("prixTotal").innerHTML = etat.totalPortefeuille.toFixed(2) + " €";
    document.getElementById("especePortefeuille").innerHTML = "Espèces : " + etat.espece.toFixed(2) + " €";
    document.getElementById("titrePortefeuille").innerHTML = "Titres : " + etat.valeurActions.toFixed(2) + " €";
  }
  else{
    document.getElementById("prixTotal").innerHTML = "N/A";
  }
}


async function afficherToutesLesActions(iduser){
  const res = await fetch(`${API_URL}/utilisateur/${iduser}/actions`,{
    headers: {
      "Authorization": `Bearer ${getToken()}`
    }
  });
  const data = await res.json();
  afficherListeActions(data);

  const resEtat = await fetch(`${API_URL}/utilisateur/${iduser}/etat-global`, {
    headers: { "Authorization": `Bearer ${getToken()}` }
  });
  if(resEtat.ok){
    const etat = await resEtat.json();
    document.getElementById("prixTotal").innerHTML = etat.totalPortefeuille.toFixed(2) + " €";
    document.getElementById("especePortefeuille").innerHTML = "Espèces : " + etat.espece.toFixed(2) + " €";
    document.getElementById("titrePortefeuille").innerHTML = "Titres : " + etat.valeurActions.toFixed(2) + " €";
  }
  else{
    document.getElementById("prixTotal").innerHTML = "N/A";
  }
}

async function afficherListeActions(data){

  //---Tableau---
  tbody.innerHTML = "";
  
  for (const a of data.actions) {
    const tr = document.createElement("tr");

    const tdNomAction = document.createElement("td");
    tdNomAction.textContent = a.nomaction;

    const tdQuantite = document.createElement("td");
    tdQuantite.textContent = a.quantiteaction;

    const tdPrixAchat = document.createElement("td");
    tdPrixAchat.textContent = a.prixachataction;

    const tdPrixActuel = document.createElement("td");
    const res = await fetch(`${API_URL}/quote/${a.symbol}`, {
      headers: {
        "Authorization": `Bearer ${getToken()}`
      }
    });
    const dataPrix = await res.json();
    if(dataPrix && typeof dataPrix.prix === "number"){
      tdPrixActuel.textContent = dataPrix.prix.toFixed(2);
    }
    else{
      tdPrixActuel.textContent = "-";
    }

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
    tr.appendChild(tdPrixAchat);
    tr.appendChild(tdPrixActuel);
    tr.appendChild(tdGainJourEuro);
    tr.appendChild(tdGainJourPourcent);
    tr.appendChild(tdGainTotalEuro);
    tr.appendChild(tdGainTotalPourcent);

    tbody.appendChild(tr);
  };

  // --- Cotation action ---
  remplirGainTableau(data, tbody);
  
}


async function remplirGainTableau(data, tbody){
  let totalInvesti = 0;
  let totalActuel = 0;
  let totalGainEuro = 0;

  const promises = data.actions.map(async (a, index) =>{
    const res = await fetch(`${API_URL}/quote/${a.symbol}`,{
      headers: {
        "Authorization": `Bearer ${getToken()}`
      }
    });
    if(!res.ok)return;

    const prixActuelData = await res.json();
    const prixActuel = prixActuelData.prix;
    const prixPrecedent = prixActuelData.prixPrecedent;

    const prixAchat = parseFloat(a.prixachataction);
    const quantite = a.quantiteaction;
    
    const fraisTotal = parseFloat(a.fraistotal || 0);

    console.log("Frais transaction total : " + fraisTotal)
    if(a.symbol == "IPS.PA"){
      console.log("Frais Ipsos : " + fraisTotal)
    }
    else if (a.symbol == "MC.PA"){
      console.log("Frais LVMH : " + fraisTotal)
    }
    else if (a.symbol == "TTE.PA"){
      console.log("Frais Total : " + fraisTotal)
    }
    
    const valeurAchat = (prixAchat * quantite) + fraisTotal;
    const valeurActuelle = prixActuel * quantite;

    const gainTotalEuro = valeurActuelle - valeurAchat;
    let gainTotalPourcent = 0;
    if(valeurAchat >0){
      gainTotalPourcent = (gainTotalEuro / valeurAchat) * 100;
    }

    const gainJourEuro = (prixActuel - prixPrecedent) * quantite;
    const gainJourPourcent = ((prixActuel / prixPrecedent) - 1) * 100;

    totalInvesti += valeurAchat;
    totalActuel += valeurActuelle;
    totalGainEuro += gainTotalEuro;

    const tr = tbody.children[index];
    tr.children[4].textContent = `${gainJourEuro.toFixed(2)} €`;
    tr.children[5].textContent = `${gainJourPourcent.toFixed(2)} %`;
    tr.children[6].textContent = `${gainTotalEuro.toFixed(2)} €`;
    tr.children[7].textContent = `${gainTotalPourcent.toFixed(2)} %`;

    const appliqueCouleur = (td, valeur) =>{
      td.classList.remove("positif","negatif");
      if(valeur < 0)
      {
        td.classList.add("negatif");
      }
      else if(valeur > 0)
      {
        td.classList.add("positif");
      }
    };

    appliqueCouleur(tr.children[4], gainJourEuro);
    appliqueCouleur(tr.children[5], gainJourPourcent);
    appliqueCouleur(tr.children[6], gainTotalEuro);
    appliqueCouleur(tr.children[7], gainTotalPourcent);
  });

  await Promise.all(promises)

  let gainPourcentTotal;
  if(totalInvesti > 0){
    gainPourcentTotal = ((totalActuel / totalInvesti) - 1 ) *100;
  }
  else{
    gainPourcentTotal = 0
  }

  remplirCarteValorisation(totalGainEuro, gainPourcentTotal);
}

function remplirCarteValorisation(valorisationEuro, valorisationPourcent){
  const txtValorisationEuro = document.getElementById("valorisationEuro");
  const txtValorisationPourcent = document.getElementById("valorisationPourcent");

  txtValorisationEuro.classList.remove("positif", "negatif");
  txtValorisationPourcent.classList.remove("positif", "negatif");

  if(valorisationEuro<0){
    txtValorisationEuro.classList.add("negatif");
  }
  else{
    txtValorisationEuro.classList.add("positif");
  }

  if(valorisationPourcent<0){
    txtValorisationPourcent.classList.add("negatif");
  }
  else{
    txtValorisationPourcent.classList.add("positif");
  }

  txtValorisationEuro.textContent = valorisationEuro.toFixed(2) + " €";
  txtValorisationPourcent.textContent = valorisationPourcent.toFixed(2) + " %";
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
  dateJourDefault("inputDatePremierVersement");
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

  const utilisateur = await getUtilisateurActuel();
  
  const res = await fetch(`${API_URL}/portefeuille`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getToken()}`},
    body: JSON.stringify({
      idutilisateur: parseInt(utilisateur.idutilisateur),
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
  const utilisateur = await getUtilisateurActuel()

  const res = await fetch(`${API_URL}/utilisateur/${utilisateur.idutilisateur}/portefeuilles`,{
    headers: {
      "Authorization": `Bearer ${getToken()}`
    }
  });
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

let LISTE_RECHERCHE = [];

document.getElementById("nomAction").addEventListener("input", async (e) =>{
  const recherche = e.target.value.trim();
  if(recherche.length < 2) return;

  const res = await fetch(`${API_URL}/rechercheActions?nom=${recherche}`, {
      headers: {
        "Authorization": `Bearer ${getToken()}`
      }
    });
  const data = await res.json();
  LISTE_RECHERCHE = data;

  const datalist = document.getElementById("listeActions");

  datalist.innerHTML = "";
  data.forEach(a =>{
    const option = document.createElement("option");
    option.value = `${a.symbol} - ${a.name}`;
    datalist.appendChild(option);
  });
});

document.getElementById("nomAction").addEventListener("change", (e) =>{
  const valeurChoisie = e.target.value;
  const trouvee = LISTE_RECHERCHE.find(a => valeurChoisie.startsWith(a.symbol));
  if(trouvee){
    document.getElementById("symbolAction").value = trouvee.symbol;
  }
  else{
    document.getElementById("symbolAction").value = "";
  }
});


//----MODALE-----
const btnAchatAction = document.getElementById("achatAction");
const modalAchat = document.getElementById("modalAchatAction");
const fermerModalAchat = document.getElementById("fermerModalAchat");
const formAchatAction = document.getElementById("formAchatAction");

btnAchatAction.addEventListener("click", function (e) {
  chargerListePortefeuille("selectPortefeuilleActionAchat");
  dateJourDefault("inputDateAchat");
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
    headers: 
    {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getToken()}`
    },
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
    const data = await res.json();
    const idaction = data.id;
    alert("Action ajouté ! ");
    const typeTransactionAchat = "ACHAT"
    
    await enregistrerTransaction(dateAchatActionValue, typeTransactionAchat, quantiteActionValue, montantInitActionValue, idaction, idportefeuilleValue);
    
    modalAchat.style.display = "none";
    
    if(portefeuilleActifID)
    {
      suppressionPortefeuille.style.display = "block";
      afficherActions(parseInt(portefeuilleActifID));

      const interval = localStorage.getItem("interval");
      afficherGraphiqueEvolutionGenerique(`${API_URL}/portefeuille/${parseInt(portefeuilleActifID)}/evolution?interval=${interval}`)
    }
    else
    {
      suppressionPortefeuille.style.display = "none";
      const utilisateur = await getUtilisateurActuel()
      afficherToutesLesActions(utilisateur.idutilisateur);

      const interval = localStorage.getItem("interval");
      afficherGraphiqueEvolutionGenerique(`${API_URL}/utilisateur/${utilisateur.idutilisateur}/evolution?interval=${interval}`)

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

  const res = await fetch(`${API_URL}/portefeuille/${choixPortefeuille}/actions`,{
    headers: {
      "Authorization": `Bearer ${getToken()}`
    }
  });

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
  dateJourDefault("inputDateVente");
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

  let portefeuilleActifID = localStorage.getItem("portefeuilleActifID");
  let idaction = parseInt(document.getElementById("selectActionVendre").value);
  const quantite = parseInt(e.target.quantiteActionVente.value);
  const dateVente = e.target.dateVenteAction.value;
  const prixVente = parseFloat(e.target.montantVenteAction.value);
  let idportefeuilleValue = parseInt(document.getElementById("selectPortefeuilleActionVente").value)

  if(!idaction || !quantite || quantite <= 0){
    alert("Selectioner une action et une quantité valide")
    return;
  } 

  const confirmation = confirm("Voulez-vous vraiment vendre cette action ?")
  if(!confirmation) return;

  const res = await fetch(`${API_URL}/action/${idaction}?quantite=${quantite}&prix_vente=${prixVente}`, {
    method: "DELETE",
  });

  if(res.ok){
    alert("Action vendu !")
    await enregistrerTransaction(dateVente, "VENTE", quantite, prixVente, idaction, idportefeuilleValue);

    modalVente.style.display = "none";

    
    if(portefeuilleActifID)
    {
      afficherActions(parseInt(portefeuilleActifID));

      const interval = localStorage.getItem("interval");
      afficherGraphiqueEvolutionGenerique(`${API_URL}/portefeuille/${parseInt(portefeuilleActifID)}/evolution?interval=${interval}`) 
    }
    else
    {
      const utilisateur = await getUtilisateurActuel()
      afficherToutesLesActions(utilisateur.idutilisateur);

      const interval = localStorage.getItem("interval");
      afficherGraphiqueEvolutionGenerique(`${API_URL}/utilisateur/${utilisateur.idutilisateur}/evolution?interval=${interval}`)
    }
  }
  else{
    alert("Erreur lors de la vente")
  }
})


async function enregistrerTransaction(date, type, quantite, prix, idaction, idportefeuille) {
  const res = await fetch(`${API_URL}/transaction`, {
    method: "POST",
    headers: 
    {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      datetransaction: date,
      typetransaction: type,
      quantitetransaction: quantite,
      prixtransaction: prix,
      idaction: idaction,
      idportefeuille: idportefeuille
    })
  });
}


// ---------------------------
// --- GRAPHIQUE EVOLUTION ---
// ---------------------------

let chartEvolution = null;

async function afficherGraphiqueEvolutionGenerique(url) {
  const res = await fetch(url, {
    headers: { "Authorization": `Bearer ${getToken()}` }
  });


  if(!res.ok){
    const err = await res.text();
    console.error("Erreur API : ", err)
    return;
  }

  const data = await res.json();
  const labels = data.map(d => d.date);
  const valeur = data.map(d => d.performance);

  const ctx = document.getElementById("graphEvolution").getContext("2d");

  const chartData = {
    labels: labels,
    datasets: [{
      data: valeur,
      tension: 0.5,
      borderWidth: 2,
      borderColor: '#0099FF',
      fill: false,
      pointRadius:0
    }]
  };

  const chartOptions = {
    responsive: true,
    scales: {
      y:{
        ticks: {
          callback: function(value){
            return value + ' %'
          }
        }
      },
      x:{
        ticks:{
          display: false
        },
          grid: {
          display: false
        },
      }
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        enabled: true,
        mode: 'index',
        intersect: false,
        callbacks: {
          label: function(context) {
            return context.formattedValue + ' %';
          }
        }
      }
    },
    interaction: {
      mode: 'index',
      intersect: false
    }
  }

  if(chartEvolution){
    chartEvolution.data = chartData;
    chartEvolution.option = chartOptions;
    chartEvolution.update();
  }
  else{
    chartEvolution = new Chart(ctx, {
      type: 'line',
      data: chartData,
      options: chartOptions
    });
  }
}

async function chargerGraphiqueSelonFiltre(interval) {
  const idportefeuille = localStorage.getItem("portefeuilleActifID");
  console.log("ID portefeuile : ddd" , idportefeuille)

  if (idportefeuille){
    await afficherGraphiqueEvolutionGenerique(`${API_URL}/portefeuille/${idportefeuille}/evolution?interval=${interval}`)
  }
  else {
    const utilisateur = await getUtilisateurActuel()
    await afficherGraphiqueEvolutionGenerique(`${API_URL}/utilisateur/${utilisateur.idutilisateur}/evolution?interval=${interval}`);
  }
}

// --- Filtre Jour/Mois ---

filtreEvolutionJour = document.getElementById("filtreEvolutionJour");
filtreEvolutionMois = document.getElementById("filtreEvolutionMois");

filtreEvolutionJour.addEventListener('click', function (e) {
  e.preventDefault();
  localStorage.setItem("interval", "1d")
  chargerGraphiqueSelonFiltre("1d");
})

filtreEvolutionMois.addEventListener('click', function (e) {
  e.preventDefault();
  localStorage.setItem("interval", "1mo")
  chargerGraphiqueSelonFiltre("1mo");
})



// -------------------------------
// --- AJOUT/RETRAIT LIQUIDITE ---
// -------------------------------


const gestionLiquidite = document.getElementById("gestionLiquidite");

const modalLiquidite = document.getElementById("modalLiquidite");
const fermerModalLiquidite = document.getElementById("fermerModalLiquidite");

const formAjoutLiquidite = document.getElementById("formAjoutLiquidite");


gestionLiquidite.addEventListener("click", () =>{
  chargerListePortefeuille("selectTypePortefeuilleLiquidite");
  chargerListeTypeOperation();
  dateJourDefault("inputDateOperation");

  modalLiquidite.style.display = "block"
})

fermerModalLiquidite.addEventListener("click", function (e) {
  modalLiquidite.style.display = "none";
});

window.addEventListener("click", function (e) {
  if (e.target === modalLiquidite) {
    modalLiquidite.style.display = "none";
  }
});

function chargerListeTypeOperation() {
  const selectTypeOperation = document.getElementById("selectTypeOperation");
  selectTypeOperation.innerHTML = "";

  const options = ["Virement entrant","Virement sortant","Ajuster les montants"];

  options.forEach(opt =>{
    const option = document.createElement("option");
    option.value = opt;
    option.textContent = opt;
    selectTypeOperation.appendChild(option);
  })
}

function dateJourDefault(inputDateParametre) {
  const inputDate = document.getElementById(inputDateParametre);
  inputDate.value = new Date().toISOString().split('T')[0];
}

document.getElementById("selectTypeOperation").addEventListener("change", function(){
  const info = document.getElementById("infoAjustement")
  if(this.value === "Ajuster les montants"){
    info.style.display = "block";
  }
  else{
    info.style.display = "none";
  }
})


formAjoutLiquidite.addEventListener("submit", async function (e) {
  e.preventDefault();

  let idportefeuilleValue = parseInt(document.getElementById("selectTypePortefeuilleLiquidite").value)
  let typeOperation = e.target.typeOperation.value;
  let selectTypeOperation;
  if(typeOperation === "Virement entrant")
  {
    selectTypeOperation = "entrant";
  }
  else if (typeOperation === "Ajuster les montants")
  {
    selectTypeOperation = "ajuster";
  }
  else
  {
    selectTypeOperation = "sortant";
  }


  let montant = e.target.montantLiquidite.value;
  let date = e.target.dateOperation.value;

  if(isNaN(montant) || montant <= 0){
    alert("veuillez rentrer un montant valide");
    return
  }


  const res = await fetch(`${API_URL}/liquidite`, {
    method: "POST",
    headers: 
    {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      dateliquidite: date,
      montantliquidite: montant,
      typeliquidite: selectTypeOperation,
      idportefeuille: idportefeuilleValue
    })
  });

  if(res.ok){
    alert("Liquidité enregistrée !");
    modalLiquidite.style.display = "none";

    // Recharge l'état du portefeuille global affiché
    const idPortefeuilleActif = localStorage.getItem("portefeuilleActifID");
    if (idPortefeuilleActif) {
      await afficherEtatPortefeuille(parseInt(idPortefeuilleActif));
    }
    else{
      const utilisateur = await getUtilisateurActuel()
      await afficherEtatGlobalPortefeuille(utilisateur.idutilisateur)
    }
  }
  else{
    const err = await res.json();
    alert("Erreur : " + (err.detail || "lors de l'enregistrement"));
  }
})

async function afficherEtatPortefeuille(id) {
  const res = await fetch(`${API_URL}/portefeuille/${id}/etat`, {
      headers: { "Authorization": `Bearer ${getToken()}` }
  });
  if (!res.ok) {
    alert("Erreur lors du chargement de l’état du portefeuille");
    return;
  }
  const data = await res.json();
  document.getElementById("prixTotal").textContent = data.totalPortefeuille.toFixed(2) + " €";
  document.getElementById("especePortefeuille").innerHTML = "Espèces : " + data.espece.toFixed(2) + " €";
  document.getElementById("titrePortefeuille").innerHTML = "Titres : " + data.valeurActions.toFixed(2) + " €";
}

async function afficherEtatGlobalPortefeuille(id) {
  const res = await fetch(`${API_URL}/utilisateur/${id}/etat-global`, {
      headers: { "Authorization": `Bearer ${getToken()}` }
  });
  if (!res.ok) {
      alert("Erreur lors du chargement de l’état du portefeuille");
      return;
  }
  const data = await res.json();
  document.getElementById("prixTotal").textContent = data.totalPortefeuille.toFixed(2) + " €";
  document.getElementById("especePortefeuille").innerHTML = "Espèces : " + data.espece.toFixed(2) + " €";
  document.getElementById("titrePortefeuille").innerHTML = "Titres : " + data.valeurActions.toFixed(2) + " €";
}