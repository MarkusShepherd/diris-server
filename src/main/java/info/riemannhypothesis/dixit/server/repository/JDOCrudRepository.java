package info.riemannhypothesis.dixit.server.repository;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import javax.jdo.PersistenceManager;
import javax.jdo.Query;

public class JDOCrudRepository<T, ID extends Serializable> {

    private Class<T> type_;

    public JDOCrudRepository(Class<T> type) {
        type_ = type;
    }

    public <S extends T> S save(S entity) {
        return PMF.get().getPersistenceManager().makePersistent(entity);
    }

    public <S extends T> Iterable<S> save(Iterable<S> entities) {
        List<S> saved = new ArrayList<S>();
        for (S entity : entities) {
            saved.add(save(entity));
        }
        return saved;
    }

    public T update(ID id, Callback<T> callback) {
        PersistenceManager pm = PMF.get().getPersistenceManager();
        T e;
        try {
            e = pm.getObjectById(type_, id);
            callback.apply(e);
        } finally {
            pm.close();
        }
        return e;
    }

    public T findOne(ID id) {
        return (T) PMF.get().getPersistenceManager().getObjectById(type_, id);
    }

    public boolean exists(ID id) {
        return findOne(id) != null;
    }

    @SuppressWarnings("unchecked")
    public Iterable<T> findAll() {
        Query query = PMF.get().getPersistenceManager().newQuery(type_);
        Object rslt = query.execute();
        return (Collection<T>) rslt;
    }

    public void delete(ID id) {
        T obj = findOne(id);
        if (obj != null) {
            PMF.get().getPersistenceManager().deletePersistent(obj);
        }
    }

    public void delete(T entity) {
        PMF.get().getPersistenceManager().deletePersistent(entity);
    }

    public interface Callback<T> {
        public void apply(T element);
    }
}