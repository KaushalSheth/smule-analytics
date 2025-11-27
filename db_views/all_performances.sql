drop view all_performances;
CREATE OR REPLACE VIEW all_performances AS
SELECT  p.*,
        split_part(p.key::text, '_'::text, 1) AS instance_key,
        COALESCE(s.performed_by, p.owner_handle) AS partner_name,
        COALESCE(s.pic_url, p.owner_pic_url) AS partner_pic_url,
        case when pf.rating_nbr >= 8 then 1 else 0 end favorite_ind,
        pf.rating_nbr,
        case when owner_handle = 'KaushalSheth1' and web_url not like '%ensembles' and ensemble_type != 'SOLO' then 1 else 0 end join_ind
FROM    performance p
        left outer join singer s on s.performed_by = p.performers
        left join performance_favorite pf on pf.performance_key = p.key
;
