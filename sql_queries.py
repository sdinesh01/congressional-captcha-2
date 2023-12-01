SQL_BILLS_BUILD = """
            CREATE TABLE tBills
            (   
                bill_id INTEGER NOT NULL PRIMARY KEY,
                bill_number INTEGER NOT NULL,
                title TEXT,
                description TEXT,
                state TEXT NOT NULL, 
                session TEXT NOT NULL, 
                filename TEXT NOT NULL, 
                status INTEGER,
                status_date TEXT, 
                error TEXT,
                content TEXT,
                processed_at TIMESTAMP,
                url TEXT 
            );"""

SQL_FULL_BILLS_BUILD = """
            CREATE TABLE tBills
            (
                bill_id INTEGER NOT NULL PRIMARY KEY,
                code TEXT,
                bill_number INTEGER NOT NULL,
                title TEXT,
                description TEXT,
                state TEXT NOT NULL, 
                session TEXT NOT NULL, 
                filename TEXT NOT NULL, 
                status INTEGER,
                status_date TEXT, 
                error TEXT,
                content TEXT, 
                processed_at TIMESTAMP,
                url TEXT 
            );"""

SQL_CHECK_BILLS = """
            SELECT bill_id
            FROM tBills
            WHERE bill_number = :bill_number
                AND title = :title
                AND description = :description
                AND state = :state
                AND session = :session
                AND filename = :filename
                AND status = :status
                AND status_date = :status_date
                AND url = :url
            ;"""

SQL_INSERT_TBILLS = """
            INSERT INTO tBills (
                            bill_id,
                            code,
                            bill_number,
                            title,
                            description, 
                            state,
                            session,
                            filename, 
                            status, 
                            status_date,
                            url, 
                            error,
                            processed_at,
                            content)
            VALUES (:bill_id,
                    :code,
                    :bill_number,
                    :title,
                    :description,
                    :state, 
                    :session, 
                    :filename, 
                    :status, 
                    :status_date, 
                    :url,
                    :error,
                    :processed_at,
                    :content
                    )
            ;"""
