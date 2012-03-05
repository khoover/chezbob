



CREATE TABLE fp_fingers (

    -- fingerprint ID used in all messages
    fp_id              INT NOT NULL AUTO_INCREMENT,

    -- record paramenters
    rec_expires        DATETIME NOT NULL,
    rec_added       DATETIME NOT NULL,
    rec_uid            VARCHAR(255) NOT NULL,
    rec_finger         VARCHAR(255) NOT NULL,

    -- match parameters
    m_ok            INT NOT NULL,      -- nonzero = OK to match againts this rec
    m_count            INT NOT NULL,      -- number of successful matches
    m_last_time        DATETIME NOT NULL, -- time of last match
    m_last_sim        INT NOT NULL,       -- similarity of last match
    m_last_g        INT NOT NULL,      -- G of the other fingerprint

    -- fingerprint data (g + features)
    fp_g              INT NOT NULL,
    fp_data               BLOB NOT NULL,

    PRIMARY KEY k_prim(fp_id),
    KEY k_o_g(m_ok, fp_g),
    KEY k_u(rec_uid),
    KEY k_tm_exp(rec_expires)
);

