from fastapi import FastAPI, Depends, HTTPException, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, create_engine
from database import SessionLocal, engine, Base
from models import Portefeuille, Utilisateur, Action, TypePortefeuille, Plateforme, Transaction
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import date
from dotenv import load_dotenv
import yfinance as yf
import requests
import os


#=============================================
#=================PARAMETRAGE=================
#=============================================
# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

# Créer l'app FastAPI
app = FastAPI()

# Autoriser les appels
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à adapter pour Vercel plus tard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



#============================================================
#=====================LISTE ACTION FINNHUB===================
#============================================================
load_dotenv()
EOD_API_KEY = os.getenv("EOD_API_KEY")

@app.get("/listeActions")
def getListeActionParis():
    url = f"https://eodhd.com/api/exchange-symbol-list/PA?api_token={EOD_API_KEY}&fmt=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # selectionne que actions :
        actions = [
            {"symbol": d["Code"] + ".PA", "name": d["Name"]}
            for d in data
            if d.get("Type", "").lower() in ["common stock", "equity"]
        ]
        return actions[:500]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Finnhub : {str(e)}")



#===================================================
#=====================UTILISATEUR===================
#===================================================

@app.get("/utilisateur")
def get_utilisateurs(db: Session = Depends(get_db)):
    utilisateurs = db.query(Utilisateur).all()
    return [
        {
            "idutilisateur": u.idutilisateur, 
            "nomutilisateur": u.nomutilisateur, 
            "prenomutilisateur":u.prenomutilisateur, 
            "emailutilisateur":u.emailutilisateur,
            "motsdepasseutilisateur":u.motsdepasseutilisateur,
            "estadmin":u.estadmin
        } 
        for u in utilisateurs]

@app.get("/utilisateur/{id}")
def get_utilisateur_id(id: int, db: Session = Depends(get_db)):
    utilisateur = db.query(Utilisateur).filter_by(idutilisateur=id).first()
    return {
        "idutilisateur": utilisateur.idutilisateur, 
        "nomutilisateur": utilisateur.nomutilisateur, 
        "prenomutilisateur":utilisateur.prenomutilisateur,
        "emailutilisateur":utilisateur.emailutilisateur,
        "motsdepasseutilisateur":utilisateur.motsdepasseutilisateur,
        "estadmin":utilisateur.estadmin,
    }


#====================================================
#=====================PORTEFEUILLE===================
#====================================================

@app.get("/portefeuille")
def get_portefeuilles(db: Session = Depends(get_db)):
    portefeuilles = db.query(Portefeuille).all()
    return [
        {
            "idportefeuille": p.idportefeuille, 
            "idutilisateur": p.idutilisateur, 
            "nomportefeuille": p.nomportefeuille,
            "totalportefeuille": float(p.totalportefeuille)
        } 
        for p in portefeuilles]

#====Route portefeuilles par utilisateur=====
@app.get("/utilisateur/{id}/portefeuilles")
def get_portefeuilles_par_utilisateur(id: int, db: Session = Depends(get_db)):
    portefeuilles = db.query(Portefeuille).filter_by(idutilisateur=id).all()
    return [
        {
            "idportefeuille":p.idportefeuille,
            "nomportefeuille":p.nomportefeuille,
            "totalportefeuille":float(p.totalportefeuille)
        } 
        for p in portefeuilles]


#====Ajout portefeuille=====
class PorteFeuilleInput(BaseModel):
    idutilisateur: int
    nomportefeuille: str
    totalportefeuille: float
    dateouverture: date
    idtypeportefeuille: int
    idplateforme: int

@app.post("/portefeuille")
def ajout_portefeuille(data: PorteFeuilleInput, db: Session = Depends(get_db)):
    nouveauPortefeuille = Portefeuille(
        idutilisateur=data.idutilisateur,
        nomportefeuille=data.nomportefeuille,
        totalportefeuille=data.totalportefeuille,
        dateouverture=data.dateouverture,
        idtypeportefeuille=data.idtypeportefeuille,
        idplateforme=data.idplateforme
    )
    db.add(nouveauPortefeuille)
    db.commit()
    db.refresh(nouveauPortefeuille)
    return{"message":"Portefeuille ajouté", "id":nouveauPortefeuille.idportefeuille}


#====Suppression portefeuille=====
@app.delete("/portefeuille/{id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_portefeuille(id: int, db: Session = Depends(get_db)):
    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=id).first()
    if not portefeuille:
        raise HTTPException(status_code=404, detail="Portefeuille non trouvé")
    
    db.delete(portefeuille)
    db.commit()
    return




#==============================================
#=====================ACTION===================
#==============================================

@app.get("/action")
def get_actions(db: Session = Depends(get_db)):
    actions = db.query(Action).all()
    return [
        {
            "idaction": a.idaction,
            "idportefeuille": a.idportefeuille,
            "nomaction": a.nomaction,
            "symbol": a.symbol,
            "quantiteaction":a.quantiteaction, 
            "dateachataction":a.dateachataction,
            "prixachataction":a.prixachataction
        } 
        for a in actions]

@app.get("/portefeuille/{id}/actions")
def get_actions_par_portefeuille(id: int, db: Session = Depends(get_db)):
    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=id).first()
    actions = db.query(Action).filter_by(idportefeuille=id).all()
    return {
        "totalportefeuille": float(portefeuille.totalportefeuille),
        "actions":[
            {
                "idaction":a.idaction,
                "nomaction":a.nomaction,
                "symbol":a.symbol,
                "prixachataction":a.prixachataction,
                "quantiteaction":a.quantiteaction
            } 
        
        for a in actions]
    }

#Toutes les actions
@app.get("/utilisateur/{id}/actions")
def get_actions_tous_portefeuilles(id: int, db: Session = Depends(get_db)):

    portefeuilles = db.query(Portefeuille).filter_by(idutilisateur=id).all()

    total = sum([float(p.totalportefeuille) for p in portefeuilles])

    ids = [p.idportefeuille for p in portefeuilles]
    actions = db.query(Action).filter(Action.idportefeuille.in_(ids)).all()

    return {
        "totalportefeuille":total,
        "actions":[
            {
                "idaction":a.idaction,
                "nomaction":a.nomaction,
                "symbol":a.symbol,
                "prixachataction":a.prixachataction,
                "quantiteaction":a.quantiteaction,
            }
            for a in actions
        ]
    }

#===Ajout Action===
class ActionInput(BaseModel):
    nomaction: str
    symbol: str
    quantiteaction: int
    dateachataction: date
    prixachataction: float
    idportefeuille: int

@app.post("/action")
def ajout_action(data: ActionInput, db: Session = Depends(get_db)):

    action_existante = db.query(Action).filter(
        and_(
            Action.symbol == data.symbol,
            Action.idportefeuille == data.idportefeuille
        )
    ).first()

    if action_existante:
        q_old = action_existante.quantiteaction
        p_old = float(action_existante.prixachataction)

        q_new = data.quantiteaction
        p_new = float(data.prixachataction)

        # Calculer la moyenne des actions pour pouvoir les cumuler
        q_total = q_old + q_new
        p_moyen = ((p_old*q_old) + (p_new*q_new))/q_total

        action_existante.quantiteaction = q_total
        action_existante.dateachataction = data.dateachataction
        action_existante.prixachataction = p_moyen

        db.commit()
        return {"message": "Action mise a jour", "id":action_existante.idaction}

    nouvelleAction = Action(
        nomaction=data.nomaction,
        symbol=data.symbol,
        quantiteaction=data.quantiteaction,
        dateachataction=data.dateachataction,
        prixachataction=data.prixachataction,
        idportefeuille=data.idportefeuille,
    )

    db.add(nouvelleAction)
    db.commit()
    db.refresh(nouvelleAction)
    return{"message":"Action ajoutée", "id":nouvelleAction.idaction}


#====Suppression action=====
@app.delete("/action/{id}", status_code=status.HTTP_204_NO_CONTENT)
def vendre_action(id: int, quantite: int = Query(..., gt=0), db: Session = Depends(get_db)):
    action = db.query(Action).filter_by(idaction=id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvé")
    
    if quantite > action.quantiteaction:
        raise HTTPException(status_code=400, detail="Quantité vendu supperieur à celle possedée")
    
    action.quantiteaction -= quantite
    if action.quantiteaction == 0:
        db.delete(action)

    db.commit()
    return

#=============================================
#=====================LOGIN===================
#=============================================

# que pour POST (évite async, ...)
class LoginData(BaseModel):
    emailutilisateur: str
    motsdepasseutilisateur: str

# Route post login
@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):

    user = db.query(Utilisateur).filter_by(
        emailutilisateur=data.emailutilisateur,
        motsdepasseutilisateur=data.motsdepasseutilisateur 
    ).first()

    if user:
        return {
            "idUtilisateur":user.idutilisateur,
            "emailutilisateur":user.emailutilisateur,
            "motsdepasseutilisateur":user.motsdepasseutilisateur
        }
    else:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")


#===================================================
#=====================INSCRIPTION===================
#===================================================
class InscriptionData(BaseModel):
    prenomutilisateur: str
    nomutilisateur: str
    emailutilisateur: str
    motsdepasseutilisateur: str

@app.post("/inscription")
def login(data: InscriptionData, db: Session = Depends(get_db)):

    userExistant = db.query(Utilisateur).filter_by(emailutilisateur=data.emailutilisateur).first()

    if userExistant:
       raise HTTPException(status_code=400, detail="Email déja utilisé")

    nouvel_utilisateur = Utilisateur(
        prenomutilisateur=data.prenomutilisateur,
        nomutilisateur=data.nomutilisateur,
        emailutilisateur=data.emailutilisateur,
        motsdepasseutilisateur=data.motsdepasseutilisateur
    )

    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)

    return {"message":"Inscription réussie", "idUtilisateur": nouvel_utilisateur.idutilisateur}


#=========================================================
#=====================TYPE PORTEFEUILLE===================
#=========================================================
@app.get("/type-portefeuille")
def get_type_portefeuille(db: Session = Depends(get_db)):
    typePortefeuille = db.query(TypePortefeuille).all()
    return [
        {
            "idtypeportefeuille":t.idtypeportefeuille,
            "nomtypeportefeuille":t.nomtypeportefeuille,
            "fraisfiscauxtypeportefeuille":float(t.fraisfiscauxtypeportefeuille)
        } 
        for t in typePortefeuille]

#==================================================
#=====================PLATEFORME===================
#==================================================
@app.get("/plateforme")
def get_plateforme(db: Session = Depends(get_db)):
    plateforme = db.query(Plateforme).all()
    return [
        {
            "idplateforme":p.idplateforme,
            "nomplateforme":p.nomplateforme,
            "fraisfixe":float(p.fraisfixe),
            "fraispercent":float(p.fraispercent)
        } 
        for p in plateforme]

#===================================================
#=====================TRANSACTION===================
#===================================================
@app.get("/transaction")
def get_transaction(db: Session = Depends(get_db)):
    transaction = db.query(Transaction).all()
    return [
        {
            "idtransaction":t.idtransaction,
            "datetransaction":t.datetransaction,
            "typetransaction":t.typetransaction,
            "quantitetransaction":t.quantitetransaction,
            "prixtransaction":float(t.prixtransaction),
            "idaction":t.idaction,
        } 
        for t in transaction]


#====Ajout Transaction=====
class TransactionInput(BaseModel):
    datetransaction: date
    typetransaction: str
    quantitetransaction: int
    prixtransaction: float
    idaction: int

@app.post("/transaction")
def ajout_transaction(data: TransactionInput, db: Session = Depends(get_db)):
    nouvelleTransaction = Transaction(
        datetransaction=data.datetransaction,
        typetransaction=data.typetransaction,
        quantitetransaction=data.quantitetransaction,
        prixtransaction=data.prixtransaction,
        idaction=data.idaction
    )
    db.add(nouvelleTransaction)
    db.commit()
    db.refresh(nouvelleTransaction)
    return{"message":"Transaction ajouté", "id":nouvelleTransaction.idtransaction}


#=======================================================
#=====================COTATION ACTION===================
#=======================================================

@app.get("/quote/{symbol}")
def get_cotation_actuelle(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        historique = stock.history(period="2d")

        if len(historique)<2:
            raise HTTPException(status_code=400, detail="Pas assez de données pour ce symbole")

        prix_hier = historique["Close"].iloc[-2]
        prix_aujourdhui = historique["Close"].iloc[-1]

        return {"symbol": symbol, "prix": round(float(prix_aujourdhui), 2),  "prixPrecedent":round(float(prix_hier), 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récuperation de prix : {str(e)}")



#====================================================
#=======================CONNEXION====================
#====================================================

# Pour servir les fichiers HTML/CSS/JS classiques
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
