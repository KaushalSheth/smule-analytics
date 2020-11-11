CREATE OR REPLACE VIEW my_favorites AS
SELECT  pf.favorited_by_username,
        pf.performance_key,
        pf.created_at,
        pf.updated_at,
        s.performed_by AS partner_name,
        count(pf.performance_key) OVER (PARTITION BY s.account_id) AS partner_favorite_cnt
FROM    performance_favorite pf
        JOIN performance p ON p.key = pf.performance_key
        JOIN performance_singer ps ON ps.performance_key = p.key
        JOIN singer s ON s.account_id = ps.singer_account_id
WHERE   pf.favorited_by_username = 'KaushalSheth1'
AND     s.performed_by <> 'KaushalSheth1'
;
