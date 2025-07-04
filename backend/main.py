from fastapi import FastAPI, Depends, HTTPException, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import SessionLocal, engine
from models import Portefeuille, Utilisateur, Action, TypePortefeuille, Plateforme, Base
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import date
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
            "emailutilisateur":u.emailutilisateur
        } 
        for u in utilisateurs]

@app.get("/utilisateur/{id}")
def get_utilisateur_id(id: int, db: Session = Depends(get_db)):
    utilisateur = db.query(Utilisateur).filter_by(idutilisateur=id).first()
    return {
        "idutilisateur": utilisateur.idutilisateur, 
        "nomutilisateur": utilisateur.nomutilisateur, 
        "prenomutilisateur":utilisateur.prenomutilisateur, 
        "emailutilisateur":utilisateur.emailutilisateur
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
            "idplateforme": a.idplateforme,
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
        q_total = q_old + p_new
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
    nomutilisateur: str
    prenomutilisateur: str

# Route login
@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    nom = data.nomutilisateur
    prenom = data.prenomutilisateur

    user = db.query(Utilisateur).filter_by(
        nomutilisateur=nom,
        prenomutilisateur=prenom 
    ).first()

    if user:
        return {
            "idUtilisateur":user.idutilisateur,
            "nom":user.nomutilisateur,
            "prenom":user.prenomutilisateur
        }
    else:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")


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


#====================================================
#=======================CONNEXION====================
#====================================================

# Pour servir les fichiers HTML/CSS/JS classiques
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
