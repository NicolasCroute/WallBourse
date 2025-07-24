from fastapi import FastAPI, Depends, HTTPException, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, create_engine, func, desc
from database import SessionLocal, engine, Base
from models import Portefeuille, Utilisateur, Action, TypePortefeuille, Plateforme, Transaction, Liquidite
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, date
from dotenv import load_dotenv
from decimal import Decimal
from ttf import TTF_ISIN_LIST
from session import utilisateur_connecte_id
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import yfinance as yf
import requests
import logging
import bcrypt
import os
import jwt
import traceback
import datetime



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
    allow_origins=["*"],
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




#=============================================
#=====================LOGIN===================
#=============================================

# que pour POST (évite async, ...)
class LoginData(BaseModel):
    emailutilisateur: str
    motsdepasseutilisateur: str

SECRET_KEY = "votre_cle_secrete_super_securite"

# Route post login
@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    global utilisateur_connecte_id

    user = db.query(Utilisateur).filter_by(emailutilisateur=data.emailutilisateur).first()
    
    if user and bcrypt.checkpw(data.motsdepasseutilisateur.encode('utf-8'), user.motsdepasseutilisateur.encode('utf-8')):
        payload={
            "sub": str(user.idutilisateur),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        
        return {"access_token": token, "estadmin": user.estadmin}
    else:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")


#=====================================================
#=====================GESTION DROIT===================
#=====================================================
auth_scheme = HTTPBearer()

def getUtilisateurActuel(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        user = db.query(Utilisateur).filter_by(idutilisateur=user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expirée")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")
    

def adminRequis(user: Utilisateur = Depends(getUtilisateurActuel)):
    if not user.estadmin:
        raise HTTPException(status_code=403, detail="Accès interdit (admin uniquement)")
    return user

@app.get("/utilisateur/mes-donnees")
def get_me(user: Utilisateur = Depends(getUtilisateurActuel)):
    return{
        "idutilisateur": user.idutilisateur,
        "nomutilisateur": user.nomutilisateur,
        "prenomutilisateur": user.prenomutilisateur,
        "estadmin": user.estadmin
    }

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
    
    hashed_pwd = bcrypt.hashpw(data.motsdepasseutilisateur.encode('utf-8'), bcrypt.gensalt())

    nouvel_utilisateur = Utilisateur(
        prenomutilisateur=data.prenomutilisateur,
        nomutilisateur=data.nomutilisateur,
        emailutilisateur=data.emailutilisateur,
        motsdepasseutilisateur=hashed_pwd.decode('utf-8'),
        estadmin = False
    )

    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)

    return {"message":"Inscription réussie", "idUtilisateur": nouvel_utilisateur.idutilisateur}


#============================================================
#=====================LISTE ACTION FINNHUB===================
#============================================================
load_dotenv()
EOD_API_KEY = os.getenv("EOD_API_KEY")

@app.get("/rechercheActions")
def rechercheAction(nom: str, user: Utilisateur = Depends(getUtilisateurActuel)):
    try:
        url = f"https://eodhd.com/api/search/{nom}?api_token={EOD_API_KEY}&fmt=json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # selectionne que actions :
        actions=[]
        for d in data:
            if d.get("Type", "").lower() in["common stock", "equity"]:
                exchange = d.get("Exchange")
                code = d.get("Code")

                if exchange == "PA":
                    symbol = f"{code}.PA"
                else:
                    symbol = code
                
                actions.append({
                    "symbol": symbol,
                    "name":d.get("Name")
                })
        return actions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recherche : {str(e)}")



#===================================================
#=====================UTILISATEUR===================
#===================================================

@app.get("/utilisateur")
def get_utilisateurs(db: Session = Depends(get_db), user: Utilisateur = Depends(adminRequis)):
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
def get_utilisateur_id(id: int, db: Session = Depends(get_db), user: Utilisateur = Depends(getUtilisateurActuel)):
    if user.idutilisateur != id and not user.estadmin:
        raise HTTPException(status_code=403, detail="Accès interdit")
    
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
def get_portefeuilles(db: Session = Depends(get_db), user: Utilisateur = Depends(adminRequis)):
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
def get_portefeuilles_par_utilisateur(id: int, db: Session = Depends(get_db), user: Utilisateur = Depends(getUtilisateurActuel)):
    if user.idutilisateur != id and not user.estadmin:
        raise HTTPException(status_code=403, detail="Accès interdit")
    
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
def get_actions(db: Session = Depends(get_db), user: Utilisateur = Depends(adminRequis)):
    actions = db.query(Action).all()
    return [
        {
            "idaction": a.idaction,
            "idportefeuille": a.idportefeuille,
            "nomaction": a.nomaction,
            "symbol": a.symbol,
            "quantiteaction":a.quantiteaction, 
            "dateachataction":a.dateachataction,
            "prixachataction":a.prixachataction,
            "actionvendu":a.actionvendu
        } 
        for a in actions]

@app.get("/portefeuille/{id}/actions")
def get_actions_par_portefeuille(id: int, db: Session = Depends(get_db), user: Utilisateur = Depends(getUtilisateurActuel)):
    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=id).first()

    if user.idutilisateur != portefeuille.idutilisateur and not user.estadmin:
        raise HTTPException(status_code=403, detail="Accès interdit")

    actions = db.query(Action).filter_by(idportefeuille=id, actionvendu=False).all()
    return {
        "totalportefeuille": float(portefeuille.totalportefeuille),
        "actions":[
            {
                "idaction":a.idaction,
                "nomaction":a.nomaction,
                "symbol":a.symbol,
                "prixachataction":a.prixachataction,
                "quantiteaction":a.quantiteaction,
                "actionvendu":a.actionvendu,
                "fraistotal": (db.query(Transaction.fraistransaction).filter(Transaction.idaction == a.idaction).order_by(Transaction.datetransaction.desc()).first() or (0,))[0]
            } 
        
        for a in actions]
    }

#Toutes les actions
@app.get("/utilisateur/{id}/actions")
def get_actions_tous_portefeuilles(id: int, db: Session = Depends(get_db), user: Utilisateur = Depends(getUtilisateurActuel)):
    if user.idutilisateur != id and not user.estadmin:
        raise HTTPException(status_code=403, detail="Accès interdit")

    portefeuilles = db.query(Portefeuille).filter_by(idutilisateur=id).all()

    total = sum([float(p.totalportefeuille) for p in portefeuilles])

    ids = [p.idportefeuille for p in portefeuilles]
    actions = db.query(Action).filter(Action.idportefeuille.in_(ids), Action.actionvendu == False).all()
    
    return {
        "totalportefeuille":total,
        "actions":[
            {
                "idaction":a.idaction,
                "nomaction":a.nomaction,
                "symbol":a.symbol,
                "prixachataction":a.prixachataction,
                "quantiteaction":a.quantiteaction,
                "actionvendu":a.actionvendu,
                "fraistotal": db.query(Transaction.fraistransaction).filter(Transaction.idaction == a.idaction).order_by(Transaction.datetransaction.desc()).first()[0] or 0
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
    #logique verif si fond necessaire :
    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=data.idportefeuille).first()
    montant_achat = Decimal(str(data.quantiteaction)) * Decimal(str(data.prixachataction))
    if (portefeuille.especeportefeuille or Decimal("0")) < montant_achat:
        HTTPException(status_code=400, detail="Fonds insuffisant pour cet achat")
    
    portefeuille.especeportefeuille = portefeuille.especeportefeuille - montant_achat

    action_existante = db.query(Action).filter(
        and_(
            Action.symbol == data.symbol,
            Action.idportefeuille == data.idportefeuille
        )
    ).first()

    if action_existante:
        if action_existante.actionvendu:
            # on écrase les anciennes valeurs par les nouvelles :
            action_existante.actionvendu = False
            action_existante.quantiteaction = data.quantiteaction
            action_existante.dateachataction = data.dateachataction
            action_existante.prixachataction = data.prixachataction
        else:
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
def vendre_action(id: int, quantite: int = Query(..., gt=0), prix_vente: float = Query(...), db: Session = Depends(get_db)):
    action = db.query(Action).filter_by(idaction=id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvé")
    
    if quantite > action.quantiteaction:
        raise HTTPException(status_code=400, detail="Quantité vendu supperieur à celle possedée")
    
    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=action.idportefeuille).first()
    montant_vente = quantite * prix_vente
    montant_vente = Decimal(str(montant_vente))
    portefeuille.especeportefeuille = (portefeuille.especeportefeuille or Decimal("0")) + montant_vente

    action.quantiteaction -= quantite

    if action.quantiteaction == 0:
        action.actionvendu = True

    db.commit()
    return
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
            "nomplateforme":p.nomplateforme
        } 
        for p in plateforme]

#===================================================
#=====================TRANSACTION===================
#===================================================
@app.get("/transaction")
def get_transaction(db: Session = Depends(get_db), user: Utilisateur = Depends(adminRequis)):
    transaction = db.query(Transaction).all()
    return [
        {
            "idtransaction":t.idtransaction,
            "datetransaction":t.datetransaction,
            "typetransaction":t.typetransaction,
            "quantitetransaction":t.quantitetransaction,
            "prixtransaction":float(t.prixtransaction),
            "fraistransaction":float(t.fraistransaction),
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
    idportefeuille: int

EOD_API_KEY = os.getenv("EOD_API_KEY")

@app.post("/transaction")
def ajout_transaction(data: TransactionInput, db: Session = Depends(get_db)):
    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=data.idportefeuille).first()
    plateforme = db.query(Plateforme).filter_by(idplateforme=portefeuille.idplateforme).first()
    
    frais = 0.0

    if data.typetransaction.upper() == "ACHAT":
        montantOrdre = data.quantitetransaction * data.prixtransaction

        if plateforme.nomplateforme.lower() == "bourse direct":
            frais = calculerFraisTransactionBourseDirecte(montantOrdre)
        
        action = db.query(Action).filter_by(idaction=data.idaction).first()
        if action:
            try:
                url = f"https://eodhd.com/api/search/{action.symbol}?api_token={EOD_API_KEY}&fmt=json"
                response = requests.get(url)
                response.raise_for_status()
                results = response.json()

                # trouver l’ISIN correspondant
                for r in results:
                    codeActionFrancais = r.get("Code") + ".PA"
                    if codeActionFrancais  == action.symbol:
                        isin = r.get("ISIN")
                        if isin:
                            print(f"[TTF] ISIN pour {action.symbol} : {isin}")
                            if isin in TTF_ISIN_LIST:
                                seuil_ttf = datetime.datetime.strptime("01/04/2025", "%d/%m/%Y").date()
                                print(seuil_ttf)
                                if action.dateachataction <= seuil_ttf:
                                    taxe_ttf = montantOrdre * 0.003
                                else:
                                    taxe_ttf = montantOrdre * 0.004
                                frais += taxe_ttf
                                print(f"[TTF] Appliquée : {taxe_ttf:.2f} €")
                                print(f"[TTF] frais : {frais:.2f} €")
                        break
            except Exception as e:
                print(f"[TTF] Erreur récupération ISIN via EODHD : {e}")

    nouvelleTransaction = Transaction(
        datetransaction=data.datetransaction,
        typetransaction=data.typetransaction,
        quantitetransaction=data.quantitetransaction,
        prixtransaction=data.prixtransaction,
        fraistransaction=frais,
        idaction=data.idaction
    )
    db.add(nouvelleTransaction)
    db.commit()
    db.refresh(nouvelleTransaction)
    return{"message":"Transaction ajouté", "id":nouvelleTransaction.idtransaction}


def calculerFraisTransactionBourseDirecte(montant: float) -> float:
    if montant < 500:
        return 0.99
    elif montant < 1000:
        return 1.90
    elif montant < 2000:
        return 2.90
    elif montant > 4400:
        return round(montant * 0.0009, 2)
    else:
        return 3.90

#=======================================================
#=====================COTATION ACTION===================
#=======================================================

@app.get("/quote/{symbol}")
def get_cotation_actuelle(symbol: str, user: Utilisateur = Depends(getUtilisateurActuel)):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        prix_aujourdhui = info.get("regularMarketPrice")
        prix_hier = info.get("previousClose")

        if prix_aujourdhui is None or prix_hier is None:
            raise HTTPException(status_code=400, detail="Pas assez de données pour ce symbole")

        return {"symbol": symbol, "prix": round(float(prix_aujourdhui), 2),  "prixPrecedent":round(float(prix_hier), 2)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récuperation de prix : {str(e)}")


#=====================================================
#=======================EVOLUTION=====================
#=====================================================
prix_cache = {}

@app.get("/portefeuille/{id}/evolution")
def get_portefeuille_evolution(id: int, interval: str = Query("1mo", enum=["1mo", "1d"]), db: Session = Depends(get_db), user: Utilisateur = Depends(getUtilisateurActuel)):

    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=id).first()
    actions = db.query(Action).filter_by(idportefeuille=id, actionvendu=False).all()

    if not actions:
        return []

    historique = defaultdict(lambda: {"valeur_marche": 0.0, "cout_achat": 0.0})
    start_date = min(a.dateachataction for a in actions).replace(day=1)
    end_date = datetime.datetime.today().date()

    for a in actions:

        key = (a.symbol, start_date, end_date, interval)
        if key in prix_cache:
            prixs = prix_cache[key]
        else:
            prixs = yf.download(a.symbol, start=start_date, end=end_date, interval=interval)
            prix_cache[key] = prixs

        montant_achat_total= get_cout_achat_avec_frais(a, db)

        for date_str, row in prixs.iterrows():
            if interval == "1mo":
                date = date_str.date().replace(day=1)
            else:
                date = date_str.date()
            
            if date >= a.dateachataction:
                close_price = float(row['Close'])
                if isinstance(close_price, dict):
                    close_price = close_price.get(a.symbol, 0)
                valeur_actuelle = close_price * a.quantiteaction
                historique[date]["valeur_marche"] += valeur_actuelle
                historique[date]["cout_achat"] += montant_achat_total
    
    resultat = []
    for date, valeurs in sorted(historique.items()):
        achat = valeurs["cout_achat"]
        valeur = valeurs["valeur_marche"]
        if achat > 0:
            performance = ((valeur - achat) / achat) * 100
            resultat.append({
                "date": date.strftime("%Y-%m-%d") if interval == "1d" else date.strftime("%Y-%m"),
                "performance": round(performance, 2)
            })

    return resultat


@app.get("/utilisateur/{id}/evolution")
def get_utilisateur_evolution(id: int, interval: str = Query("1mo", enum=["1mo", "1d"]), db: Session = Depends(get_db), user: Utilisateur = Depends(getUtilisateurActuel)):
    portefeuilles = db.query(Portefeuille).filter_by(idutilisateur=id).all()
    if not portefeuilles:
        return []

    historique = defaultdict(lambda: {"valeur_marche": 0.0, "cout_achat": 0.0})
    end_date = datetime.datetime.today().date()

    for p in portefeuilles:
        actions = db.query(Action).filter_by(idportefeuille=p.idportefeuille, actionvendu=False).all()
        if not actions:
            continue

        start_date = min(a.dateachataction for a in actions).replace(day=1)

        for a in actions:
            key = (a.symbol, start_date, end_date, interval)
            if key in prix_cache:
                prixs = prix_cache[key]
            else:
                prixs = yf.download(a.symbol, start=start_date, end=end_date, interval=interval)
                prix_cache[key] = prixs

            montant_achat_total= get_cout_achat_avec_frais(a, db)

            for date_str, row in prixs.iterrows():
                if interval == "1mo":
                    date = date_str.date().replace(day=1)
                else:
                    date = date_str.date()
                if date >= a.dateachataction:
                    close_price = float(row['Close'])
                    if isinstance(close_price, dict):
                        close_price = close_price.get(a.symbol, 0)
                    valeur_actuelle = close_price * a.quantiteaction
                    historique[date]["valeur_marche"] += valeur_actuelle
                    historique[date]["cout_achat"] += montant_achat_total
    
    resultat = []
    for date, valeurs in sorted(historique.items()):
        achat = valeurs["cout_achat"]
        valeur = valeurs["valeur_marche"]
        if achat > 0:
            performance = ((valeur - achat) / achat) * 100
            resultat.append({
                "date": date.strftime("%Y-%m-%d") if interval == "1d" else date.strftime("%Y-%m"),
                "performance": round(performance, 2)
            })

    return resultat



#==================================================================
#=======================METHODE GENERIQUE FRAIS====================
#==================================================================

def get_cout_achat_avec_frais(action: Action, db: Session) -> float:
    montant_achat = float(action.prixachataction) * action.quantiteaction
    transaction = db.query(Transaction).filter(Transaction.idaction == action.idaction).order_by(Transaction.datetransaction.desc()).first()
    frais = float(transaction.fraistransaction) if transaction and transaction.fraistransaction else 0
    
    print("transaction : ", transaction.fraistransaction, " idtransaction : " , transaction.idtransaction)
    print("frais : ", frais)
    return montant_achat + frais


#====================================================
#=======================LIQUIDITE====================
#====================================================

@app.get("/liquidite")
def get_liquidite(db: Session = Depends(get_db), user: Utilisateur = Depends(adminRequis)):
    liquidite = db.query(Liquidite).all()

    return[{
        "idliquidite": l.idliquidite,
        "dateliquidite": l.dateliquidite,
        "montantliquidite": l.montantliquidite,
        "typeliquidite": l.typeliquidite,
    }
    for l in liquidite]



class LiquiditeInput(BaseModel):
    dateliquidite: date
    montantliquidite: float
    typeliquidite: str
    idportefeuille: int

@app.post("/liquidite")
def ajout_liquidite(data: LiquiditeInput, db: Session = Depends(get_db), user: Utilisateur = Depends(adminRequis)):
    montant = Decimal(str(data.montantliquidite))
    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=data.idportefeuille).first()
    if not portefeuille:
        raise HTTPException(status_code=404, detail="Portefeuille introuvable")

    if data.typeliquidite == "sortant":
        montant = -montant

        if portefeuille.especeportefeuille + montant < 0:
            raise HTTPException(status_code=400, detail="Fond insufisant pour le retrait")
    
    portefeuille.especeportefeuille = (portefeuille.especeportefeuille or 0) + montant
    
    liquidite = Liquidite(
        dateliquidite=data.dateliquidite,
        montantliquidite=data.montantliquidite,
        typeliquidite=data.typeliquidite,
        idportefeuille=data.idportefeuille
    )
    db.add(liquidite)
    db.commit()

    return {"message":"Opération enregistrée", "especeportefeuille": float(portefeuille.especeportefeuille)}


@app.get("/portefeuille/{id}/etat")
def get_etat_portefeuille(id: int, db: Session = Depends(get_db), user: Utilisateur = Depends(getUtilisateurActuel)):
    portefeuille = db.query(Portefeuille).filter_by(idportefeuille=id).first()
    if not portefeuille:
        raise HTTPException(status_code=404, detail="Portefeuille non trouvé")
    return calcul_etat_portefeuille(portefeuille, db)

@app.get("/utilisateur/{id}/etat-global")
def get_etat_portefeuille(id: int, db: Session = Depends(get_db), user: Utilisateur = Depends(getUtilisateurActuel)):
    portefeuilles = db.query(Portefeuille).filter_by(idutilisateur=id).all()
    if not portefeuilles:
        raise HTTPException(status_code=404, detail="Aucun portefeulle trouvé")
    
    total_epece = 0
    total_valeur_actions = 0
    total_investi = 0

    for p in portefeuilles:
        etat = calcul_etat_portefeuille(p, db)
        total_epece += etat["espece"]
        total_valeur_actions += etat["valeurActions"]
        total_investi += etat["totalInvesti"]
    
    
    total_portefeuille = total_epece + total_valeur_actions

    return{
        "espece": round(total_epece, 2),
        "valeurActions": round(total_valeur_actions, 2),
        "totalPortefeuille": round(total_portefeuille, 2),
        "totalInvesti": round(total_investi, 2)
    }
    

def calcul_etat_portefeuille(portefeuille, db):
    actions = db.query(Action).filter_by(idportefeuille=portefeuille.idportefeuille, actionvendu=False).all()
    valeur_actions = 0
    total_pru = 0

    for a in actions:
        try:
            import yfinance as yf
            stock = yf.Ticker(a.symbol)
            info = stock.info
            prix_marche = info.get("regularMarketPrice", 0) or 0
        except:
            prix_marche = 0

        montant_achat_total = get_cout_achat_avec_frais(a, db)
        valeur_actuelle = prix_marche * a.quantiteaction
        valeur_actions += valeur_actuelle
        total_pru += montant_achat_total

    especeportefeuille = float(portefeuille.especeportefeuille or 0)
    total_portefeuille = especeportefeuille + valeur_actions

    return {
        "espece": round(especeportefeuille, 2),
        "valeurActions": round(valeur_actions, 2),
        "totalPortefeuille": round(total_portefeuille, 2),
        "totalInvesti": round(total_pru, 2)
    }




#====================================================
#=======================CONNEXION====================
#====================================================

# Pour servir les fichiers HTML/CSS/JS classiques
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
