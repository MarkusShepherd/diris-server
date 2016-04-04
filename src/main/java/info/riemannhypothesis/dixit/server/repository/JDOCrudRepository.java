package info.riemannhypothesis.dixit.server.repository;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.LinkedList;
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

	public <S extends T> List<S> save(Iterable<S> entities) {
		List<S> saved = new ArrayList<S>();
		for (S entity : entities)
			saved.add(save(entity));
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

	public T findById(ID id) {
		return PMF.get().getPersistenceManager().getObjectById(type_, id);
	}

	@SuppressWarnings("unchecked")
	public List<T> findByIds(List<ID> ids) {
		if (ids.isEmpty())
			return new LinkedList<T>();

		Query query = PMF.get().getPersistenceManager().newQuery(type_);
		query.setFilter(":p.contains(key)");
		return (List<T>) query.execute(ids);
	}

	public boolean exists(ID id) {
		return findById(id) != null;
	}

	@SuppressWarnings("unchecked")
	public List<T> findAll() {
		Query query = PMF.get().getPersistenceManager().newQuery(type_);
		return (List<T>) query.execute();
	}

	public List<T> findAll(long maxResults) {
		return findAll(0, maxResults);
	}

	@SuppressWarnings("unchecked")
	public List<T> findAll(long from, long to) {
		Query query = PMF.get().getPersistenceManager().newQuery(type_);
		query.setRange(from, to);
		return (List<T>) query.execute();
	}

	@SuppressWarnings("unchecked")
	public List<T> findByField(String field, String parameter) {
		Query query = PMF.get().getPersistenceManager().newQuery(type_);
		query.setFilter(field + " == p");
		query.declareParameters("String p");
		return (List<T>) query.execute(parameter);
	}

	public List<T> findByField(String field, String parameter, long maxResults) {
		return findByField(field, parameter, 0, maxResults);
	}

	@SuppressWarnings("unchecked")
	public List<T> findByField(String field, String parameter, long from,
			long to) {
		Query query = PMF.get().getPersistenceManager().newQuery(type_);
		query.setFilter(field + " == p");
		query.declareParameters("String p");
		query.setRange(from, to);
		return (List<T>) query.execute(parameter);
	}

	public void delete(ID id) {
		T obj = findById(id);
		if (obj != null)
			PMF.get().getPersistenceManager().deletePersistent(obj);
	}

	public void delete(T entity) {
		PMF.get().getPersistenceManager().deletePersistent(entity);
	}

	public interface Callback<T> {
		public void apply(T element);
	}
}