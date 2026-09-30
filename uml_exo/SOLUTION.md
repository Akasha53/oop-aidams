# UML practice : solution (slide 68)

Énoncé : https://gist.github.com/bdallard/2d2407c4de4c182afca6d3ec7235e9eb

Les diagrammes sont en Mermaid (rendu direct dans GitHub, VS Code, Obsidian ou https://mermaid.live).
L'implémentation Python suit les diagrammes :

```bash
python3 hospital.py        # démo exo 1
python3 abcd_records.py    # démo exo 2
python3 -m unittest -v     # 14 tests
```

---

## Exo 1 : Hospital Management System

### Task 1 : les trois acteurs

```mermaid
classDiagram
    class Patient {
        -id: str
        -name: str
        -password: str
        -email: str
        +postProblem(description) 
        +pay(amount, method)
        +viewPrescription()
    }
    class Organizer {
        -id: str
        -name: str
        -password: str
        +consultDoctor(problem, doctor)
        +sendPrescription(patient)
        +forwardPayment(doctor)
        +registerMember()
    }
    class Doctor {
        -id: str
        -name: str
        -password: str
        -specialty: str
        +providePrescription(problem)
        +receivePayment(amount)
    }
    Patient "1..*" -- "1" Organizer : submits problems / pays
    Organizer "1" -- "1..*" Doctor : consults / pays
```

Le patient ne parle jamais directement au médecin : tout passe par l'organizer. Un seul organizer gère plusieurs patients et plusieurs médecins.

### Task 2 et Task 3 : diagramme complet

Ajouts de la Task 3 intégrés ici : superclasse `User`, statut du problème, horodatages, lien vers une ordonnance antérieure, paiement par polymorphisme (Strategy).

```mermaid
classDiagram
    direction LR
    class User {
        <<abstract>>
        #id: str
        #name: str
        #passwordHash: str
        #loggedIn: bool
        +login(password) bool
        +logout()
    }
    class Patient {
        -email: str
        +postProblem(description) HealthProblem
        +receivePrescription(rx)
        +pay(rx, method) Payment
        +history() List~Prescription~
    }
    class Doctor {
        -specialty: str
        -balance: float
        +review(problem)
        +writePrescription(problem, content, fee, basedOn) Prescription
        +receivePayment(amount)
    }
    class Organizer {
        +registerPatient(...) Patient
        +registerDoctor(...) Doctor
        +consult(problem, doctor)
        +sendPrescription(rx)
        +forwardPayment(payment)
    }
    class HospitalSystem {
        -users: Map~id, User~
        +addUser(user)
        +find(id) User
    }
    class HealthProblem {
        -id: str
        -description: str
        -status: ProblemStatus
        -createdAt: datetime
        +setStatus(status)
    }
    class ProblemStatus {
        <<enumeration>>
        PENDING
        IN_REVIEW
        RESOLVED
    }
    class Prescription {
        -id: str
        -content: str
        -fee: float
        -createdAt: datetime
        -deliveredAt: datetime
    }
    class Payment {
        -id: str
        -amount: float
        -status: PaymentStatus
        -reference: str
        -paidAt: datetime
        -forwardedAt: datetime
        +process()
        +forwardTo(doctor)
    }
    class PaymentStatus {
        <<enumeration>>
        PENDING
        COMPLETED
        FORWARDED
    }
    class PaymentMethod {
        <<interface>>
        +charge(amount) str
    }
    class CashPayment
    class CheckPayment {
        -checkNumber: str
        -bank: str
    }
    class CreditCardPayment {
        -last4: str
        -expiry: str
    }

    User <|-- Patient
    User <|-- Doctor
    User <|-- Organizer
    HospitalSystem "1" o-- "*" User : stores
    Organizer "1" --> "1" HospitalSystem : administers
    Patient "1" *-- "*" HealthProblem : posts
    HealthProblem "*" --> "0..1" Doctor : assigned to
    HealthProblem "1" *-- "*" Prescription : answered by
    Doctor "1" <-- "*" Prescription : written by
    Prescription "0..1" --> "0..1" Prescription : basedOn
    Prescription "1" -- "0..1" Payment : settled by
    Payment --> PaymentMethod : strategy
    PaymentMethod <|.. CashPayment
    PaymentMethod <|.. CheckPayment
    PaymentMethod <|.. CreditCardPayment
    HealthProblem --> ProblemStatus
    Payment --> PaymentStatus
```

Choix de modélisation :

- Composition `Patient *-- HealthProblem` : un problème n'existe pas sans le patient qui l'a posté. Même chose pour `HealthProblem *-- Prescription`.
- Agrégation `HospitalSystem o-- User` : le système référence les utilisateurs mais ne définit pas leur existence.
- Paiement : une interface `PaymentMethod` et trois implémentations plutôt qu'une enum. Avec une enum, chaque nouveau moyen de paiement oblige à modifier un `if/elif` dans `Payment`. Avec l'interface, on ajoute une classe et rien d'autre ne change (principe ouvert/fermé).
- `CreditCardPayment` ne garde que les 4 derniers chiffres de la carte.

### Task 2 : séquence « un patient soumet un problème, reçoit une ordonnance et paie »

```mermaid
sequenceDiagram
    actor P as :Patient
    participant O as :Organizer
    participant D as :Doctor
    participant HP as :HealthProblem
    participant RX as :Prescription
    participant PAY as :Payment

    P->>HP: postProblem("Headache")
    activate HP
    Note right of HP: status = PENDING
    HP-->>P: problem
    deactivate HP

    O->>D: consult(problem)
    D->>HP: setStatus(IN_REVIEW)
    D->>RX: writePrescription(problem, content, fee)
    RX-->>D: rx
    D-->>O: rx

    O->>HP: setStatus(RESOLVED)
    O->>P: receivePrescription(rx)

    P->>PAY: pay(rx, CreditCardPayment)
    activate PAY
    PAY->>PAY: method.charge(fee)
    Note right of PAY: status = COMPLETED
    PAY-->>P: payment
    deactivate PAY

    O->>PAY: forwardTo(doctor)
    PAY->>D: receivePayment(amount)
    Note right of PAY: status = FORWARDED
```

### Task 3 : diagrammes de séquence système

Dans un SSD, le système est une boîte noire : on ne montre que les échanges entre les acteurs et `:System`.

#### 1. Patient Registration

```mermaid
sequenceDiagram
    actor O as Organizer
    participant S as :System
    actor P as Patient

    O->>S: login(id, password)
    S-->>O: ok
    O->>S: registerPatient(name, password, email)
    alt email déjà utilisé
        S-->>O: error "member exists"
    else
        S-->>O: memberId
        O->>P: send memberId + password
    end
    O->>S: logout()
```

#### 2. Consultation Flow

```mermaid
sequenceDiagram
    actor P as Patient
    participant S as :System
    actor O as Organizer
    actor D as Doctor

    P->>S: postProblem(description)
    S-->>P: problemId (PENDING)
    O->>S: listPendingProblems()
    S-->>O: problems
    O->>S: consult(problemId, doctorId)
    S-->>D: notify new case (IN_REVIEW)
    D->>S: writePrescription(problemId, content, fee)
    S-->>O: prescription ready
    O->>S: sendPrescription(rxId)
    S-->>P: prescription + fee (RESOLVED)
```

#### 3. Payment Processing

```mermaid
sequenceDiagram
    actor P as Patient
    participant S as :System
    actor O as Organizer
    actor D as Doctor

    P->>S: pay(rxId, method, details)
    alt déjà payée / montant != fee / carte refusée
        S-->>P: error
    else
        S-->>P: receipt (COMPLETED)
        O->>S: forwardPayment(paymentId)
        alt statut != COMPLETED
            S-->>O: error "cannot forward"
        else
            S-->>D: payment received
            S-->>O: ok (FORWARDED)
        end
    end
```

### Questions to consider

#### 1. Un patient qui consulte plusieurs médecins
Chaque `HealthProblem` a son propre médecin, donc un patient avec trois problèmes peut voir trois médecins. Si un même problème doit être vu par plusieurs médecins (second avis), on remplace l'association `HealthProblem --> Doctor` par une classe d'association `Consultation(problem, doctor, date, notes)` : multiplicité `HealthProblem 1 -- * Consultation * -- 1 Doctor`.

#### 2. Ordonnances réutilisables
Une ordonnance est un acte médical daté et signé : on ne la modifie pas, on ne la réutilise pas telle quelle. Pour un renouvellement, on crée une nouvelle `Prescription` avec `basedOn` pointant vers l'ancienne. On garde l'historique, et chaque renouvellement a son propre paiement. Si l'on veut des traitements types (« angine standard »), on ajoute une classe `PrescriptionTemplate` dont le médecin part pour rédiger une nouvelle ordonnance.

#### 3. Pattern pour le paiement
Strategy : `Payment` délègue `charge()` à un `PaymentMethod` interchangeable. On peut y ajouter une Factory qui construit la bonne stratégie à partir du choix de l'utilisateur (`"card"` → `CreditCardPayment`).

#### 4. Intégrité des paiements
Dans le code :
- montant contrôlé (égal à `fee`) ;
- pas de paiement avant la livraison de l'ordonnance, pas de second paiement (`prescription.payment` déjà renseigné) ;
- machine à états `PENDING → COMPLETED → FORWARDED` : on ne reverse pas deux fois le même paiement au médecin ;
- numéro de carte tronqué, mot de passe haché.

En production, il faudrait en plus une transaction en base (débit patient et crédit médecin validés ensemble ou pas du tout), une clé d'idempotence sur chaque requête de paiement, un journal d'audit en ajout seul, et un prestataire certifié PCI-DSS pour les cartes.

---

## Exo 2 : ABCD Records

### Level 1

#### Task 1.1 : use case simple

Mermaid n'a pas de diagramme de cas d'utilisation natif, on le simule avec un flowchart (ovales = cas d'utilisation).

```mermaid
flowchart LR
    M["🧍 Member"]
    C["🧍 Order Processing Clerk"]
    subgraph ABCD Records
        PO([Place Order])
        VM([Verify Membership])
        PR([Process Order])
        MP([Make Payment])
    end
    M --- PO
    M --- MP
    C --- VM
    C --- PR
```

#### Task 1.2 : classes simples

```mermaid
classDiagram
    class Member {
        -memberId: str
        -name: str
        -address: str
        -memberType: str
        +placeOrder(items) Order
        +makePayment(order)
    }
    class Order {
        -orderId: str
        -date: date
        -items: List
        -status: str
        +addItem(item, qty)
        +total() float
    }
    class OrderProcessingClerk {
        -clerkId: str
        -name: str
        +verifyMembership(member) bool
        +processOrder(order)
        +printInvoice(order)
    }
    Member "1" --> "*" Order : places
    OrderProcessingClerk "1" --> "*" Order : processes
    OrderProcessingClerk ..> Member : verifies
```

### Level 2

#### Task 2.1 : use case complet

```mermaid
flowchart LR
    M["🧍 Member"]
    R["🧍 Royal Member"]
    NM["🧍 Non-Member"]
    C["🧍 Order Processing Clerk"]
    K["🧍 Collection Dept. Clerk"]

    subgraph SYS [ABCD Records system]
        PO([Place Order])
        VM([Verify Membership])
        VA([Verify Item Availability])
        PR([Process Order])
        AD([Apply Discount])
        PI([Print Invoice])
        PS([Print Shipping List])
        OU([Order Unavailable Items])
        SA([Send Membership Application])
        MP([Make Payment])
    end

    R -->|is a| M
    M --- PO
    M --- MP
    R --- OU
    NM --- SA
    C --- PR
    K --- MP

    PO -.->|include| VM
    PR -.->|include| VA
    PR -.->|include| PI
    PR -.->|include| PS
    AD -.->|extend| PR
    OU -.->|extend| PO
    SA -.->|extend| VM
```

Lecture des relations :
- `<<include>>` : toujours exécuté. Toute commande passe par la vérification d'adhésion ; tout traitement vérifie le stock et imprime facture et bon d'expédition.
- `<<extend>>` : conditionnel, la flèche va de l'extension vers le cas de base. La remise ne s'applique que si le membre est Royal. La commande d'articles indisponibles n'est ouverte qu'aux Royal. Le formulaire d'adhésion part seulement si la vérification échoue.
- `Royal Member` hérite de `Member` (généralisation d'acteur) : il fait tout ce que fait un membre, plus « Order Unavailable Items ».

#### Task 2.2 : classes complètes

```mermaid
classDiagram
    direction LR
    class Member {
        <<abstract>>
        #memberId: str
        #name: str
        #address: str
        +discountRate: float
        +hasPriority: bool
        +canOrderUnavailable: bool
        +placeOrder(lines) Order
    }
    class RoyalMember {
        discountRate = 0.10
        hasPriority = true
        canOrderUnavailable = true
    }
    class RegularMember
    class NonMember {
        -name: str
        -address: str
        +receiveApplication(form)
    }
    class MembershipApplication {
        -id: str
        -applicantName: str
        -address: str
        -sentOn: date
    }
    class Order {
        -id: str
        -date: date
        -status: OrderStatus
        +addLine(item, qty)
        +shippableLines() List
        +total() float
    }
    class OrderLine {
        -quantity: int
        -unitPrice: float
        -backordered: bool
        +subtotal() float
    }
    class Item {
        <<abstract>>
        #code: str
        #title: str
        #artist: str
        #price: float
        #stock: int
        +isAvailable(qty) bool
        +removeStock(qty)
    }
    class CD { -tracks: int }
    class Tape { -lengthMin: int }
    class Invoice {
        -id: str
        -amount: float
        -issuedOn: date
        +print() str
    }
    class ShippingList {
        -id: str
        +print() str
    }
    class Payment {
        <<abstract>>
        #id: str
        #amount: float
        #paidOn: date
        +validate()* bool
        +pay()
    }
    class Cash
    class Check {
        -checkNumber: str
        -bank: str
    }
    class BankDraft {
        -draftNumber: str
        -issuingBank: str
    }
    class OrderProcessingClerk {
        +verifyMembership(c) bool
        +sendApplication(nm) MembershipApplication
        +checkAvailability(order)
        +processOrder(order) Invoice, ShippingList
    }
    class CollectionDepartmentClerk {
        +collect(invoice, payment)
    }
    class DailyRecordsFile {
        +save(order)
        +ordersOf(day) List~Order~
    }

    Member <|-- RoyalMember
    Member <|-- RegularMember
    Item <|-- CD
    Item <|-- Tape
    Payment <|-- Cash
    Payment <|-- Check
    Payment <|-- BankDraft

    Member "1" --> "*" Order : places
    Order "1" *-- "1..*" OrderLine
    OrderLine "*" --> "1" Item
    Order "1" -- "0..1" Invoice
    Order "1" -- "0..1" ShippingList
    Invoice "1" -- "0..1" Payment : settled by
    NonMember "1" --> "0..1" MembershipApplication
    OrderProcessingClerk ..> Order : processes
    OrderProcessingClerk ..> MembershipApplication : sends
    OrderProcessingClerk --> DailyRecordsFile : writes
    CollectionDepartmentClerk ..> Payment : collects
    DailyRecordsFile o-- "*" Order
```

`OrderLine` est la classe qui porte la quantité et le prix au moment de la commande. Sans elle, il faudrait une association N-N entre `Order` et `Item`, et un changement de prix du catalogue modifierait les anciennes commandes.

#### Scénario : un membre Royal commande 2 CD (dont un indisponible) et paie par chèque

Diagramme d'objets :

```mermaid
classDiagram
    class rita["rita : RoyalMember"] { name = "Rita" }
    class o1["o1 : Order"] { status = PAID }
    class l1["l1 : OrderLine"] {
        quantity = 1
        unitPrice = 12.0
        backordered = false
    }
    class l2["l2 : OrderLine"] {
        quantity = 1
        unitPrice = 20.0
        backordered = true
    }
    class thriller["thriller : CD"] { stock = 4 }
    class rare["rare : CD"] { stock = 0 }
    class inv["inv : Invoice"] { amount = 10.80 }
    class chk["chk : Check"] {
        checkNumber = "0012345"
        amount = 10.80
    }
    rita --> o1
    o1 *-- l1
    o1 *-- l2
    l1 --> thriller
    l2 --> rare
    o1 -- inv
    inv -- chk
```

Seul le CD disponible est facturé (12 € − 10 % = 10,80 €). L'autre est mis en réapprovisionnement et sera facturé à l'expédition.

### Level 3 : séquences

#### 1. Traitement complet d'une commande

```mermaid
sequenceDiagram
    actor M as :RoyalMember
    participant C as :OrderProcessingClerk
    participant O as :Order
    participant I as :Item
    participant F as :DailyRecordsFile
    participant K as :CollectionDeptClerk

    M->>O: placeOrder([(cd1,1),(cd2,1)])
    M->>C: submit(order)
    C->>C: verifyMembership(member)
    loop pour chaque OrderLine
        C->>I: isAvailable(qty)
        I-->>C: true / false
    end
    C->>I: removeStock(qty)
    C->>F: save(order)
    C->>O: total()
    O-->>C: 10.80
    C-->>M: Invoice + ShippingList
    M->>K: collect(invoice, Check)
    K-->>M: status = PAID
```

#### 2. Vérification d'adhésion (succès et échec)

```mermaid
sequenceDiagram
    actor Cu as Customer
    participant C as :OrderProcessingClerk
    participant DB as members

    Cu->>C: submit(order)
    C->>DB: lookup(memberId)
    alt membre connu
        DB-->>C: member
        C->>C: processOrder(order)
        C-->>Cu: Invoice + ShippingList
    else inconnu / non-membre
        DB-->>C: none
        C->>C: sendApplication(customer)
        C-->>Cu: MembershipApplication
        Note over C: status = REJECTED
    end
```

#### 3. Paiement (tous types)

```mermaid
sequenceDiagram
    actor M as Member
    participant K as :CollectionDeptClerk
    participant P as :Payment
    participant I as :Invoice

    M->>K: collect(invoice, payment)
    K->>I: already paid?
    alt montant != invoice.amount ou déjà payée
        K-->>M: error
    else
        K->>P: pay()
        P->>P: validate()
        Note right of P: Cash : amount > 0<br/>Check : n° numérique<br/>BankDraft : n° de traite présent
        alt invalide
            P-->>K: ValueError
            K-->>M: rejected
        else
            P-->>K: paidOn = today
            K->>I: payment = p
            K-->>M: receipt, order PAID
        end
    end
```

`K` appelle `pay()` sans connaître le type réel du paiement : c'est `validate()`, redéfinie dans chaque sous-classe, qui fait la différence (polymorphisme).

#### 4. Réapprovisionnement pour un membre Royal

```mermaid
sequenceDiagram
    participant C as :OrderProcessingClerk
    participant O as :Order
    participant L as :OrderLine
    participant I as :Item
    participant S as Supplier

    C->>I: isAvailable(qty)
    I-->>C: false
    C->>O: member.canOrderUnavailable?
    alt RoyalMember
        C->>L: backordered = true
        C->>S: reorder(item, qty)
        Note over C,S: plus tard, à la réception
        S-->>I: stock += qty
        C->>L: backordered = false
        C->>C: nouvelle Invoice + ShippingList pour la ligne
    else RegularMember
        C-->>O: status = REJECTED
    end
```

Dans le code, l'envoi au fournisseur est représenté par la liste `clerk.reorders` ; la réception et la seconde facture ne sont pas implémentées.
