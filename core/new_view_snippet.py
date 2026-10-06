
@login_required
def todos_check_done(request, id):
    """
    Quickly mark a task as done (and COMPLETED) from the dashboard or list,
    then redirect back to the previous page (dashboard).
    """
    if request.method == "POST":
        todo_service = TodoService(request.user)
        # Using update_status to ensure synchronization logic in service/model is respected
        # although update_status returns (success, msg)
        # We can also just get the object and save it using existing service methods or direct model access 
        # but let's stick to the service pattern if possible or just do a quick update.
        
        # Simpler approach: fetch and update directly or use service update_status
        # Service update_status requires a string status.
        success, msg = todo_service.update_status(id, "COMPLETED")
        
        # Redirect back to where the user came from, or dashboard default
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        
    return redirect('dashboard')
