from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Utilisateur(Base):
    __tablename__ = "utilisateur"

    idutilisateur = Column(Integer, primary_key=True, index=True)
    nomutilisateur = Column(String(50), nullable=False)
    prenomutilisateur = Column(String(50), nullable=False)
    emailutilisateur = Column(String(80), nullable=False)
    motsdepasseutilisateur = Column(String(50), nullable=False)

class Portefeuille(Base):
    __tablename__ = "portefeuille"

    idportefeuille = Column(Integer, primary_key=True, index=True)
    nomportefeuille = Column(String(100), unique=True, nullable=False)
    totalportefeuille = Column(DECIMAL, default=0)
    dateouverture = Column(Date, nullable=False)
    idtypeportefeuille = Column(Integer, ForeignKey("typeportefeuille.idtypeportefeuille"), nullable=False)
    idplateforme = Column(Integer, ForeignKey("plateforme.idplateforme"), nullable=False)
    idutilisateur = Column(Integer, ForeignKey("utilisateur.idutilisateur"), nullable=False)

class Action(Base):
    __tablename__ = "action"

    idaction = Column(Integer, primary_key=True, index=True)
    nomaction = Column(String(50), nullable=False)
    symbol = Column(String(10), nullable=False)
    quantiteaction = Column(Integer, nullable=False)
    dateachataction = Column(Date, nullable=False)
    prixachataction = Column(DECIMAL, nullable=False)
    idportefeuille = Column(Integer, ForeignKey("portefeuille.idportefeuille"), nullable=False)


class Plateforme(Base):
    __tablename__ = "plateforme"

    idplateforme = Column(Integer, primary_key=True, index=True)
    nomplateforme = Column(String(50), nullable=False)
    fraisfixe = Column(DECIMAL, nullable=False)
    fraispercent = Column(DECIMAL, nullable=False)

class TypePortefeuille(Base):
    __tablename__ = "typeportefeuille"

    idtypeportefeuille = Column(Integer, primary_key=True, index=True)
    nomtypeportefeuille = Column(String(50), nullable=False)
    fraisfiscauxtypeportefeuille = Column(DECIMAL, nullable=False)


class Transaction(Base):
    __tablename__ = "transaction"

    idtransaction = Column(Integer, primary_key=True, index=True)
    datetransaction = Column(Date, nullable=False)
    typetransaction = Column(String(10), nullable=False)
    quantitetransaction = Column(Integer, nullable=False)
    prixtransaction = Column(DECIMAL, nullable=False)
    idaction = Column(Integer, ForeignKey("action.idaction"), nullable=False)